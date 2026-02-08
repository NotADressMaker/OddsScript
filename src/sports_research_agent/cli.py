from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .extract.rule_extractors import (
    extract_goalies_from_text,
    extract_injuries_from_html,
    extract_line_moves,
    extract_probable_pitchers,
    extract_qb_starters,
)
from .fetch.http_client import HttpClient, filter_allowed_urls
from .output.report import ResearchReport
from .search.discover import discover_links
from .sources.registry import load_registry
from .verify.reconcile import (
    reconcile_injuries,
    reconcile_line_moves,
    reconcile_starters,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sports Web Research Agent")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--league", help="League (NHL, NBA, NFL, MLB)")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--sources",
        help="Path to YAML trusted sources file",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max URLs to fetch")
    return parser


def resolve_sources_path(league: str | None, override: str | None) -> Path:
    if override:
        return Path(override)
    if not league:
        raise ValueError("League is required when --sources is not provided")
    default_path = Path("configs") / f"sources_{league.lower()}.yaml"
    if not default_path.exists():
        raise FileNotFoundError(f"No default sources file at {default_path}")
    return default_path


def run(query: str, league: str | None, sources_path: str | None, json_output: bool, limit: int) -> str:
    sources_file = resolve_sources_path(league, sources_path)
    registry = load_registry(sources_file)
    client = HttpClient()

    try:
        discovered = discover_links(client, registry, query, league)
        urls = [item.url for item in discovered]
        urls = filter_allowed_urls(urls, registry.domains())
        urls = urls[:limit]

        injuries = []
        starters = []
        goalies = []
        probable_pitchers = []
        line_moves = []
        notes = []

        for url in urls:
            response = client.get(url)
            if not response or response.status_code >= 400:
                continue
            retrieved_at = response.retrieved_at
            html = response.text
            injuries.extend(extract_injuries_from_html(html, url, retrieved_at))
            starters.extend(extract_qb_starters(html, url, retrieved_at))
            goalies.extend(extract_goalies_from_text(html, url, retrieved_at))
            probable_pitchers.extend(extract_probable_pitchers(html, url, retrieved_at))
            line_moves.extend(extract_line_moves(html, url, retrieved_at))

        report = ResearchReport(
            query=query,
            generated_at=datetime.utcnow(),
            injuries=reconcile_injuries(registry, injuries),
            starters=reconcile_starters(registry, starters),
            goalies=goalies,
            probable_pitchers=probable_pitchers,
            line_moves=reconcile_line_moves(registry, line_moves),
            notes=notes,
        )

        if json_output:
            return json.dumps(report.to_json(), indent=2)
        return report.to_markdown()
    finally:
        client.close()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output = run(args.query, args.league, args.sources, args.json_output, args.limit)
    print(output)


if __name__ == "__main__":
    main()
