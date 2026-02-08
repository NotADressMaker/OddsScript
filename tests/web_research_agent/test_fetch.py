from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from sportsbetlang.web_research_agent.fetch import RobotsBlockedError, WebFetcher


def test_fetch_respects_robots(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /blocked")
        if request.url.path == "/blocked":
            return httpx.Response(200, text="blocked")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    fetcher = WebFetcher(
        cache_dir=tmp_path,
        user_agent="TestAgent",
        transport=transport,
    )
    with pytest.raises(RobotsBlockedError):
        fetcher.fetch("https://example.com/blocked")


def test_fetch_caches_with_etag(tmp_path: Path) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow:")
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(200, text="fresh", headers={"ETag": "abc"})
        if request.headers.get("If-None-Match") == "abc":
            return httpx.Response(304, headers={"ETag": "abc"})
        return httpx.Response(200, text="fallback")

    transport = httpx.MockTransport(handler)
    fetcher = WebFetcher(
        cache_dir=tmp_path,
        user_agent="TestAgent",
        transport=transport,
    )
    first = fetcher.fetch("https://example.com/data")
    second = fetcher.fetch("https://example.com/data")

    assert first.content == b"fresh"
    assert second.content == b"fresh"
    assert second.from_cache is True
