from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


@dataclass
class CachedResponse:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]
    retrieved_at: datetime


class HttpClient:
    def __init__(
        self,
        user_agent: str = "SportsResearchAgent/0.1",
        rate_limit_s: float = 1.0,
        timeout_s: float = 10.0,
    ) -> None:
        self._client = httpx.Client(timeout=timeout_s, headers={"User-Agent": user_agent})
        self._rate_limit_s = rate_limit_s
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._cache: dict[str, CachedResponse] = {}

    def close(self) -> None:
        self._client.close()

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    def _ensure_rate_limit(self, domain: str) -> None:
        last = self._last_request.get(domain)
        if last is None:
            return
        elapsed = time.time() - last
        if elapsed < self._rate_limit_s:
            time.sleep(self._rate_limit_s - elapsed)

    def _robots_parser(self, url: str) -> RobotFileParser:
        domain = self._get_domain(url)
        if domain in self._robots:
            return self._robots[domain]
        parser = RobotFileParser()
        robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
        try:
            response = self._client.get(robots_url)
            parser.parse(response.text.splitlines())
        except httpx.HTTPError:
            parser.parse("")
        self._robots[domain] = parser
        return parser

    def allowed(self, url: str) -> bool:
        parser = self._robots_parser(url)
        return parser.can_fetch(self._client.headers.get("User-Agent", "*"), url)

    def get(self, url: str) -> CachedResponse | None:
        if not self.allowed(url):
            return None

        domain = self._get_domain(url)
        self._ensure_rate_limit(domain)

        headers: dict[str, str] = {}
        cached = self._cache.get(url)
        if cached:
            if "etag" in cached.headers:
                headers["If-None-Match"] = cached.headers["etag"]
            if "last-modified" in cached.headers:
                headers["If-Modified-Since"] = cached.headers["last-modified"]

        try:
            response = self._client.get(url, headers=headers)
        except httpx.HTTPError:
            return None
        finally:
            self._last_request[domain] = time.time()

        if response.status_code == 304 and cached:
            return cached

        cached_response = CachedResponse(
            url=url,
            status_code=response.status_code,
            text=response.text,
            headers={k.lower(): v for k, v in response.headers.items()},
            retrieved_at=datetime.utcnow(),
        )
        self._cache[url] = cached_response
        return cached_response


def safe_domain(url: str) -> str:
    return urlparse(url).netloc


def filter_allowed_urls(urls: Iterable[str], registry_domains: set[str]) -> list[str]:
    return [url for url in urls if safe_domain(url) in registry_domains]
