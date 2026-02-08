"""Command line interface for the web research agent."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from sportsbetlang.web_research_agent.extract import extract_facts
from sportsbetlang.web_research_agent.fetch import FetchError, RobotsBlockedError, WebFetcher
from sportsbetlang.web_research_agent.output import build_summary, format_json, format_markdown
from sportsbetlang.web_research_agent.parse import is_soft_404, parse_html
from sportsbetlang.web_research_agent.search import SearchConfig, Searcher
from sportsbetlang.web_research_agent.verify import detect_contradictions, recency_score, triangulate

DEFAULT_USER_AGENT = "WebResearchAgent/1.0 (+https://example.org/agent)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compliant web research agent")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    parser.add_argument("--sources", type=str, help="Path to seed URL list")
    parser.add_argument("--sitemaps", type=str, help="Path to sitemap list")
    parser.add_argument("--rss", type=str, help="Path to RSS feed list")
    parser.add_argument("--no-external-search", action="store_true")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--cache-dir", type=str, default=".cache/web_research_agent")
    parser.add_argument("--rate-limit", type=float, default=1.0)
    parser.add_argument("--user-agent", type=str, default=DEFAULT_USER_AGENT)
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    fetcher = WebFetcher(
        cache_dir=cache_dir,
        user_agent=args.user_agent,
        rate_limit_per_domain=args.rate_limit,
    )

    try:
        config = SearchConfig(
            sitemaps=_read_url_file(args.sitemaps),
            rss_feeds=_read_url_file(args.rss),
            seed_urls=_read_url_file(args.sources),
            no_external_search=args.no_external_search,
        )
        searcher = Searcher(fetcher=fetcher, config=config)
        results = searcher.search(args.query, max_results=args.max_results)

        facts = []
        for result in results:
            try:
                fetched = fetcher.fetch(result.url)
            except RobotsBlockedError:
                continue
            except FetchError:
                continue
            if fetched.status_code in {401, 403}:
                continue
            document = parse_html(fetched.content, fetched.final_url)
            if is_soft_404(document):
                continue
            facts.extend(extract_facts(args.query, document, fetched.fetched_at))

        verification = triangulate(facts)
        contradictions = detect_contradictions(facts)
        confidence = _confidence_score(verification, contradictions)
        summary = build_summary(args.query, verification["confirmed"], verification["unconfirmed"])

        if args.as_json:
            output = format_json(args.query, summary, facts, contradictions, confidence)
        else:
            output = format_markdown(args.query, facts, contradictions, confidence)
        print(output)
    finally:
        fetcher.close()


def _read_url_file(path: str | None) -> List[str]:
    if not path:
        return []
    raw = Path(path).read_text(encoding="utf-8").splitlines()
    urls: List[str] = []
    for line in raw:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(_normalize_seed(line))
    return urls


def _normalize_seed(seed: str) -> str:
    if seed.startswith("http://") or seed.startswith("https://"):
        return seed
    path = Path(seed)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve().as_uri()


def _confidence_score(verification: dict, contradictions: Iterable[dict]) -> float:
    confirmed = len(verification["confirmed"])
    unconfirmed = len(verification["unconfirmed"])
    if confirmed == 0 and unconfirmed == 0:
        return 0.1
    base = confirmed / max(1, confirmed + unconfirmed)
    penalty = 0.1 * len(list(contradictions))
    return max(0.0, min(1.0, base - penalty + recency_score(verification["confirmed"])))
