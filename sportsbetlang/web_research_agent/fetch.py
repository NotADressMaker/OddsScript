"""HTTP fetching with robots compliance, rate limiting, retries, and caching."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class FetchError(RuntimeError):
    """Base error for fetch operations."""


class RobotsBlockedError(FetchError):
    """Raised when robots.txt disallows access."""


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: bytes
    headers: Dict[str, str]
    fetched_at: str
    from_cache: bool
    final_url: str


@dataclass
class CacheEntry:
    url: str
    status_code: int
    headers: Dict[str, str]
    stored_at: str


class DiskCache:
    """Simple disk cache keyed by URL hash."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _meta_path(self, url: str) -> Path:
        return self.cache_dir / f"{self._key(url)}.json"

    def _body_path(self, url: str) -> Path:
        return self.cache_dir / f"{self._key(url)}.body"

    def read(self, url: str) -> Optional[tuple[CacheEntry, bytes]]:
        meta_path = self._meta_path(url)
        body_path = self._body_path(url)
        if not meta_path.exists() or not body_path.exists():
            return None
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        entry = CacheEntry(
            url=metadata["url"],
            status_code=metadata["status_code"],
            headers=metadata["headers"],
            stored_at=metadata["stored_at"],
        )
        return entry, body_path.read_bytes()

    def write(self, url: str, status_code: int, headers: Dict[str, str], body: bytes) -> None:
        meta_path = self._meta_path(url)
        body_path = self._body_path(url)
        entry = {
            "url": url,
            "status_code": status_code,
            "headers": headers,
            "stored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        body_path.write_bytes(body)


class RateLimiter:
    """Token bucket rate limiter per domain."""

    def __init__(self, rate_per_second: float) -> None:
        self.rate_per_second = rate_per_second
        self._last_request: Dict[str, float] = {}

    def wait(self, domain: str) -> None:
        if self.rate_per_second <= 0:
            return
        interval = 1.0 / self.rate_per_second
        last = self._last_request.get(domain)
        now = time.monotonic()
        if last is not None:
            elapsed = now - last
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_request[domain] = time.monotonic()


class RobotsChecker:
    """Cached robots.txt fetcher."""

    def __init__(self, user_agent: str, client: httpx.Client) -> None:
        self.user_agent = user_agent
        self.client = client
        self._parsers: Dict[str, RobotFileParser] = {}

    def _fetch_parser(self, base_url: str) -> RobotFileParser:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        try:
            response = self.client.get(robots_url, follow_redirects=True, timeout=10)
        except httpx.HTTPError:
            parser.parse([])
            return parser
        if response.status_code >= 400:
            parser.parse([])
            return parser
        parser.parse(response.text.splitlines())
        return parser

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return True
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._parsers:
            self._parsers[base] = self._fetch_parser(base)
        return self._parsers[base].can_fetch(self.user_agent, url)


class WebFetcher:
    """HTTP client with caching and compliance safeguards."""

    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        rate_limit_per_domain: float = 1.0,
        timeout: float = 20.0,
        max_retries: int = 3,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.cache = DiskCache(cache_dir)
        self.rate_limiter = RateLimiter(rate_limit_per_domain)
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(headers={"User-Agent": user_agent}, transport=transport)
        self.robots = RobotsChecker(user_agent=user_agent, client=self.client)

    def fetch(self, url: str) -> FetchResult:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            path = Path(parsed.path)
            content = path.read_bytes()
            return FetchResult(
                url=url,
                status_code=200,
                content=content,
                headers={},
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                from_cache=False,
                final_url=url,
            )

        if not self.robots.can_fetch(url):
            raise RobotsBlockedError(f"Blocked by robots.txt: {url}")

        domain = parsed.netloc
        self.rate_limiter.wait(domain)

        cached = self.cache.read(url)
        headers: Dict[str, str] = {}
        if cached:
            entry, _body = cached
            if etag := entry.headers.get("etag"):
                headers["If-None-Match"] = etag
            if last_modified := entry.headers.get("last-modified"):
                headers["If-Modified-Since"] = last_modified

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url, headers=headers, follow_redirects=True)
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(2**attempt)
                continue

            if response.status_code == 304 and cached:
                entry, body = cached
                return FetchResult(
                    url=url,
                    status_code=entry.status_code,
                    content=body,
                    headers=entry.headers,
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    from_cache=True,
                    final_url=str(response.url),
                )

            if response.status_code >= 500:
                time.sleep(2**attempt)
                continue

            body = response.content
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            self.cache.write(url, response.status_code, response_headers, body)
            return FetchResult(
                url=url,
                status_code=response.status_code,
                content=body,
                headers=response_headers,
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                from_cache=False,
                final_url=str(response.url),
            )

        raise FetchError(f"Failed to fetch {url}") from last_error

    def close(self) -> None:
        self.client.close()


@dataclasses.dataclass
class CachedResponse:
    """Lightweight cached response for testing."""

    url: str
    body: bytes
    headers: Dict[str, str]
    status_code: int
