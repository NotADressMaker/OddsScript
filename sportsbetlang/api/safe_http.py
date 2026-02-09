"""Safe-by-default HTTP fetching helpers for the API."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket
from typing import Iterable, Optional
from urllib.parse import urlparse

from fastapi import HTTPException

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency
    httpx = None

PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


@dataclass(frozen=True)
class FetchConfig:
    """Configuration for safe HTTP fetching."""

    timeout_s: float
    max_bytes: int
    allowed_domains: Optional[set[str]] = None


def _resolve_host(host: str) -> Iterable[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return []
    addresses = []
    for family, _, _, _, sockaddr in info:
        if family == socket.AF_INET:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
        elif family == socket.AF_INET6:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
    return addresses


def is_private_ip(host: str) -> bool:
    """Return True when the host resolves to a private/loopback/link-local address."""

    try:
        ip = ipaddress.ip_address(host)
        addresses = [ip]
    except ValueError:
        addresses = list(_resolve_host(host))

    for addr in addresses:
        if any(addr in network for network in PRIVATE_NETWORKS):
            return True
    return False


def _domain_allowed(host: str, allowed_domains: set[str]) -> bool:
    host = host.lower().rstrip(".")
    for domain in allowed_domains:
        domain = domain.lower().rstrip(".")
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def validate_url(url: str, allowed_domains: Optional[set[str]] = None) -> None:
    """Validate URL scheme, host, and optional allowlist restrictions."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed.")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must include a hostname.")
    if is_private_ip(parsed.hostname):
        raise HTTPException(status_code=403, detail="Target URL is not allowed.")
    if allowed_domains is not None and not _domain_allowed(parsed.hostname, allowed_domains):
        raise HTTPException(status_code=403, detail="Target domain is not allowed.")


async def fetch_text(
    url: str,
    *,
    timeout_s: float,
    max_bytes: int,
    allowed_domains: Optional[set[str]] = None,
) -> str:
    """Fetch a text payload safely with size and content-type restrictions."""

    validate_url(url, allowed_domains)
    if httpx is None:  # pragma: no cover - optional dependency
        raise HTTPException(status_code=500, detail="HTTP client unavailable.")
    timeout = httpx.Timeout(timeout_s)
    headers = {"User-Agent": "SportsBetLang/1.0"}
    total = 0
    chunks: list[bytes] = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            async with client.stream("GET", url, headers=headers) as response:
                if response.status_code >= 400:
                    raise HTTPException(status_code=400, detail="Upstream request failed.")
                content_type = response.headers.get("content-type", "").lower()
                if not (
                    content_type.startswith("text/")
                    or content_type.startswith("application/json")
                ):
                    raise HTTPException(status_code=400, detail="Unsupported content type.")
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(status_code=413, detail="Response too large.")
                    chunks.append(chunk)
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=400, detail="Upstream request timed out.") from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail="Upstream request failed.") from exc

    return b"".join(chunks).decode("utf-8", errors="replace")
