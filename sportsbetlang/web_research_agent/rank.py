"""Ranking and de-duplication helpers."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="")
    return urlunparse(normalized)


def score_source(url: str) -> float:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 5.0
    if any(token in domain for token in ["who.int", "cdc.gov", "un.org"]):
        return 4.5
    if any(token in domain for token in ["nytimes.com", "reuters.com", "bbc.co"]):
        return 3.0
    if domain.endswith(".org"):
        return 2.5
    return 1.0
