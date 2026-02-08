"""Search discovery for web research agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from sportsbetlang.web_research_agent.fetch import WebFetcher
from sportsbetlang.web_research_agent.rank import normalize_url, score_source


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    source: str
    score: float = 0.0


@dataclass
class SearchConfig:
    sitemaps: List[str] = field(default_factory=list)
    rss_feeds: List[str] = field(default_factory=list)
    seed_urls: List[str] = field(default_factory=list)
    no_external_search: bool = False
    max_sitemap_urls: int = 200


class Searcher:
    """Search helper for sitemaps, RSS feeds, and seed URLs."""

    def __init__(self, fetcher: WebFetcher, config: SearchConfig) -> None:
        self.fetcher = fetcher
        self.config = config

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        results: List[SearchResult] = []
        if self.config.seed_urls:
            results.extend(self._seed_results())
        if not self.config.no_external_search:
            results.extend(self._from_sitemaps(query))
            results.extend(self._from_rss(query))

        deduped = self._dedupe_results(results)
        for result in deduped:
            result.score += score_source(result.url)
        deduped.sort(key=lambda item: item.score, reverse=True)
        return deduped[:max_results]

    def _seed_results(self) -> List[SearchResult]:
        results = []
        for url in self.config.seed_urls:
            results.append(
                SearchResult(
                    url=url,
                    title=urlparse(url).netloc or "Local file",
                    snippet="Seed URL",
                    source="seed",
                )
            )
        return results

    def _from_sitemaps(self, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not self.config.sitemaps:
            return results
        keywords = _keywords(query)
        sitemap_queue = list(self.config.sitemaps)
        seen_sitemaps = set()
        discovered_urls: List[str] = []

        while sitemap_queue and len(discovered_urls) < self.config.max_sitemap_urls:
            sitemap_url = sitemap_queue.pop(0)
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)
            response = self.fetcher.fetch(sitemap_url)
            urls, nested = _parse_sitemap(response.content)
            for nested_url in nested:
                if nested_url not in seen_sitemaps:
                    sitemap_queue.append(nested_url)
            discovered_urls.extend(urls)

        for url in discovered_urls[: self.config.max_sitemap_urls]:
            score = _match_score(url, keywords)
            if score == 0:
                continue
            results.append(
                SearchResult(
                    url=url,
                    title=urlparse(url).path.strip("/") or urlparse(url).netloc,
                    snippet="Matched sitemap URL",
                    source="sitemap",
                    score=score,
                )
            )
        return results

    def _from_rss(self, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not self.config.rss_feeds:
            return results
        keywords = _keywords(query)
        for feed_url in self.config.rss_feeds:
            response = self.fetcher.fetch(feed_url)
            entries = _parse_rss(response.content)
            for entry in entries:
                score = _match_score(entry["title"], keywords)
                if score == 0:
                    score = _match_score(entry["description"], keywords)
                if score == 0:
                    continue
                results.append(
                    SearchResult(
                        url=entry["link"],
                        title=entry["title"],
                        snippet=entry["description"],
                        source="rss",
                        score=score,
                    )
                )
        return results

    def _dedupe_results(self, results: Iterable[SearchResult]) -> List[SearchResult]:
        seen = set()
        deduped: List[SearchResult] = []
        for result in results:
            normalized = normalize_url(result.url)
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(result)
        return deduped


def _keywords(query: str) -> List[str]:
    return [token.lower() for token in query.split() if token.strip()]


def _match_score(text: str, keywords: List[str]) -> float:
    lowered = text.lower()
    return float(sum(1 for keyword in keywords if keyword in lowered))


def _parse_sitemap(content: bytes) -> tuple[List[str], List[str]]:
    urls: List[str] = []
    sitemaps: List[str] = []
    root = ET.fromstring(content)
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"
    if root.tag.endswith("sitemapindex"):
        for sitemap in root.findall(f"{namespace}sitemap"):
            loc = sitemap.findtext(f"{namespace}loc")
            if loc:
                sitemaps.append(loc.strip())
        return urls, sitemaps
    for url in root.findall(f"{namespace}url"):
        loc = url.findtext(f"{namespace}loc")
        if loc:
            urls.append(loc.strip())
    return urls, sitemaps


def _parse_rss(content: bytes) -> List[dict]:
    root = ET.fromstring(content)
    entries: List[dict] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = item.findtext("description") or ""
        entries.append({"title": title, "link": link, "description": description})
    return entries
