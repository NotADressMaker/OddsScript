"""Command line interface for training and predicting totals models."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from src.pipelines.predict_pipeline import predict_pipeline
from src.pipelines.train_pipeline import train_pipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Totals regression CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    train_parser = sub.add_parser("train", help="Train a totals model")
    train_parser.add_argument("--league", required=True)
    train_parser.add_argument("--data", required=True, type=Path)
    train_parser.add_argument("--config", required=True, type=Path)

    predict_parser = sub.add_parser("predict", help="Predict totals for upcoming games")
    predict_parser.add_argument("--league", required=True)
    predict_parser.add_argument("--historical", required=True, type=Path)
    predict_parser.add_argument("--games", required=True, type=Path)
    predict_parser.add_argument("--artifacts", required=True, type=Path)
    predict_parser.add_argument("--config", required=True, type=Path)
    predict_parser.add_argument("--line", required=False, type=float)

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.command == "train":
        result = train_pipeline(
            league=args.league,
            data_path=args.data,
            config_path=args.config,
        )
        print(result)
        return

    if args.command == "predict":
        predictions = predict_pipeline(
            league=args.league,
            historical_path=args.historical,
            upcoming_path=args.games,
            artifact_dir=args.artifacts,
            config_path=args.config,
            line=args.line,
        )
        print(predictions.to_csv(index=False))
        return

    raise ValueError("Unknown command")


if __name__ == "__main__":
    main()
