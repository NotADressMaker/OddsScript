from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..fetch.http_client import HttpClient
from ..sources.registry import SourceRegistry
from ..sources.rss import FeedEntry, fetch_feeds
from ..sources.sitemaps import SitemapEntry, fetch_sitemaps
from .query_expand import expand_query


@dataclass(frozen=True)
class DiscoveredLink:
    url: str
    title: str | None
    discovered_at: datetime


def _matches_query(text: str | None, queries: Iterable[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(query.lower() in lowered for query in queries)


def discover_links(
    client: HttpClient, registry: SourceRegistry, query: str, league: str | None
) -> list[DiscoveredLink]:
    queries = expand_query(query, league)
    discovered: list[DiscoveredLink] = []

    for source in registry.sources:
        if source.rss:
            feed_entries: list[FeedEntry] = fetch_feeds(client, source.rss)
            for entry in feed_entries:
                if _matches_query(entry.title, queries):
                    discovered.append(
                        DiscoveredLink(
                            url=entry.url,
                            title=entry.title,
                            discovered_at=entry.published_at or datetime.utcnow(),
                        )
                    )

        if source.sitemaps:
            sitemap_entries: list[SitemapEntry] = fetch_sitemaps(client, source.sitemaps)
            for entry in sitemap_entries:
                if _matches_query(entry.url, queries):
                    discovered.append(
                        DiscoveredLink(
                            url=entry.url,
                            title=None,
                            discovered_at=entry.last_modified or datetime.utcnow(),
                        )
                    )

    return discovered
