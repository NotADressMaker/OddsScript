"""CLI for running ingestion pipelines."""

from __future__ import annotations

import argparse

from sportsbetlang.ingestion.config import DEFAULT_MARKETS, PipelineConfig, SourceConfig, Tooling
from sportsbetlang.ingestion.pipelines.runner import PipelineRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SportsBetLang ingestion pipelines.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backfill = subparsers.add_parser("backfill", help="Run a backfill ingestion job")
    live = subparsers.add_parser("live", help="Run a live ingestion job")

    for sub in (backfill, live):
        sub.add_argument("--sport", required=True)
        sub.add_argument("--start", dest="start_date", required=True)
        sub.add_argument("--end", dest="end_date", required=True)
        sub.add_argument("--markets", default=",".join(DEFAULT_MARKETS))

    return parser


def main(tooling: Tooling) -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = PipelineConfig(
        sport=args.sport,
        start_date=args.start_date,
        end_date=args.end_date,
        markets=[m.strip() for m in args.markets.split(",")],
        sources=SourceConfig(),
    )

    runner = PipelineRunner(tooling)
    report = runner.run(config, mode=args.command)

    print("Pipeline run complete")
    print(f"Counts: {report.counts}")
    print(f"Data gaps: {report.data_gaps}")
    print(f"Feature preview SQL: {report.feature_preview_sql}")
    return 0

