"""
CLI tool for backtesting Elo totals model predictions.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import random
from typing import Dict, Iterable, List

from sportsbetlang.__version__ import __version__

from sportsbetlang.tools.base_tool import BaseTool
from lib.elo_totals import EloTotalsModel


@dataclass
class BacktestRow:
    home_team: str
    away_team: str
    home_score: float
    away_score: float
    date: str = ""


class EloTotalsBacktestTool(BaseTool):
    """Backtest Elo totals model predictions against historical games."""

    def __init__(self) -> None:
        super().__init__(
            name="elo-totals-backtest",
            description="Backtest Elo totals model and export predictions.",
        )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--league", default="NBA", help="League code (NBA, NFL).")
        parser.add_argument("--games", required=True, help="CSV file with game results.")
        parser.add_argument("--out", required=True, help="Output directory for reports.")
        parser.add_argument("--k", type=float, default=20.0, help="Elo K-factor.")
        parser.add_argument("--base-total", type=float, default=None, help="Override league avg total.")
        parser.add_argument("--seed", type=int, default=7, help="RNG seed for deterministic backtests.")

    def run(self, args) -> int:
        random.seed(args.seed)
        games = list(self._load_games(Path(args.games)))
        if not games:
            self.print_error("No games found in CSV.")
            return 1

        model = EloTotalsModel(
            league=args.league,
            k_factor=args.k,
            base_total=args.base_total,
        )

        predictions: List[Dict[str, float]] = []
        errors: List[float] = []

        for game in games:
            pred_total = model.predict_total(game.home_team, game.away_team)
            actual_total = game.home_score + game.away_score
            error = pred_total - actual_total
            predictions.append(
                {
                    "date": game.date,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                    "actual_total": actual_total,
                    "pred_total": pred_total,
                    "error": error,
                }
            )
            errors.append(error)
            model.update(game.__dict__)

        mae = sum(abs(err) for err in errors) / len(errors)
        rmse = (sum(err ** 2 for err in errors) / len(errors)) ** 0.5

        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "elo_totals_predictions.csv"
        self._write_predictions(out_file, predictions)
        config_payload = {"league": args.league, "k": args.k, "base_total": args.base_total, "seed": args.seed}
        config_hash = hashlib.sha256(json.dumps(config_payload, sort_keys=True).encode("utf-8")).hexdigest()
        fixtures_file = out_dir / "elo_totals_inputs.json"
        fixtures_file.write_text(json.dumps([asdict(g) for g in games], indent=2), encoding="utf-8")
        metadata = {"seed": args.seed, "version": __version__, "config_hash": config_hash, "inputs_artifact": str(fixtures_file)}
        metadata_file = out_dir / "elo_totals_metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        self.print_output(
            {
                "games": len(games),
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "predictions_csv": str(out_file),
                "metadata_json": str(metadata_file),
                "inputs_json": str(fixtures_file),
                "seed": args.seed,
                "version": __version__,
                "config_hash": config_hash,
            },
            format=args.output_format,
        )
        return 0

    def _load_games(self, path: Path) -> Iterable[BacktestRow]:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                normalized = self._normalize_row(row)
                yield BacktestRow(
                    home_team=normalized["home_team"],
                    away_team=normalized["away_team"],
                    home_score=float(normalized["home_score"]),
                    away_score=float(normalized["away_score"]),
                    date=normalized.get("date", ""),
                )

    def _normalize_row(self, row: Dict[str, str]) -> Dict[str, str]:
        mapping = {
            "home": "home_team",
            "away": "away_team",
            "home_points": "home_score",
            "away_points": "away_score",
        }
        normalized = {**row}
        for alias, canonical in mapping.items():
            if alias in normalized and canonical not in normalized:
                normalized[canonical] = normalized[alias]
        required = ["home_team", "away_team", "home_score", "away_score"]
        missing = [key for key in required if key not in normalized or normalized[key] == ""]
        if missing:
            raise ValueError(f"Missing required fields in CSV: {', '.join(missing)}")
        return normalized

    def _write_predictions(self, path: Path, rows: List[Dict[str, float]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    tool = EloTotalsBacktestTool()
    return tool.main()


if __name__ == "__main__":
    raise SystemExit(main())
