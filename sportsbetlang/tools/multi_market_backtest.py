"""
CLI tool for backtesting multi-market ratings model predictions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sportsbetlang.tools.base_tool import BaseTool
from lib.multi_market_ratings import MultiMarketRatingsModel, normalize_game_row


EDGE_THRESHOLDS = {
    "NBA": 3.0,
    "NFL": 2.0,
    "NHL": 0.4,
    "MLB": 0.7,
}


@dataclass
class BacktestRow:
    home_team: str
    away_team: str
    home_score: float
    away_score: float
    date: str = ""
    line_spread: Optional[float] = None
    line_total: Optional[float] = None


class MultiMarketBacktestTool(BaseTool):
    """Backtest multi-market ratings model predictions."""

    def __init__(self) -> None:
        super().__init__(
            name="multi-market-backtest",
            description="Backtest multi-market ratings model and export predictions.",
        )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--sport", required=True, help="Sport code (NBA, NFL, NHL, MLB).")
        parser.add_argument("--games", required=True, help="CSV file with game results.")
        parser.add_argument("--out", required=True, help="Output directory for reports.")
        parser.add_argument("--edge-threshold", type=float, default=None, help="Override edge threshold.")
        parser.add_argument(
            "--prob-threshold",
            type=float,
            default=0.55,
            help="Probability threshold for picks (default: 0.55).",
        )

    def run(self, args) -> int:
        sport = args.sport.upper()
        games = list(self._load_games(Path(args.games), sport))
        if not games:
            self.print_error("No games found in CSV.")
            return 1

        model = MultiMarketRatingsModel(sport)
        edge_threshold = (
            float(args.edge_threshold)
            if args.edge_threshold is not None
            else EDGE_THRESHOLDS.get(sport, 2.0)
        )
        prob_threshold = float(args.prob_threshold)

        predictions: List[Dict[str, Any]] = []

        for game in games:
            pred_spread = model.predict_spread(game.home_team, game.away_team)
            pred_total = model.predict_total(game.home_team, game.away_team)

            line_spread = game.line_spread
            line_total = game.line_total
            edge_spread = pred_spread - line_spread if line_spread is not None else None
            edge_total = pred_total - line_total if line_total is not None else None

            pick_spread = ""
            pick_total = ""
            result_parts: List[str] = []
            roi_units = 0.0

            if line_spread is not None:
                prob_cover = model.prob_cover(game.home_team, game.away_team, line_spread)
                prob_away_cover = model.prob_away_cover(game.home_team, game.away_team, line_spread)
                if prob_cover >= prob_threshold and edge_spread is not None and edge_spread >= edge_threshold:
                    pick_spread = "home"
                elif (
                    prob_away_cover >= prob_threshold
                    and edge_spread is not None
                    and edge_spread <= -edge_threshold
                ):
                    pick_spread = "away"

            if line_total is not None:
                prob_over = model.prob_over(game.home_team, game.away_team, line_total)
                prob_under = model.prob_under(game.home_team, game.away_team, line_total)
                if prob_over >= prob_threshold and edge_total is not None and edge_total >= edge_threshold:
                    pick_total = "over"
                elif prob_under >= prob_threshold and edge_total is not None and edge_total <= -edge_threshold:
                    pick_total = "under"

            actual_margin = game.home_score - game.away_score
            actual_total = game.home_score + game.away_score

            if pick_spread and line_spread is not None:
                if pick_spread == "home":
                    result = "win" if actual_margin > line_spread else "loss"
                else:
                    result = "win" if actual_margin < line_spread else "loss"
                if math.isclose(actual_margin, line_spread):
                    result = "push"
                result_parts.append(f"spread:{result}")
                roi_units += 0.909 if result == "win" else (-1.0 if result == "loss" else 0.0)

            if pick_total and line_total is not None:
                if pick_total == "over":
                    result = "win" if actual_total > line_total else "loss"
                else:
                    result = "win" if actual_total < line_total else "loss"
                if math.isclose(actual_total, line_total):
                    result = "push"
                result_parts.append(f"total:{result}")
                roi_units += 0.909 if result == "win" else (-1.0 if result == "loss" else 0.0)

            predictions.append(
                {
                    "date": game.date,
                    "sport": sport,
                    "home": game.home_team,
                    "away": game.away_team,
                    "line_spread": line_spread,
                    "pred_spread": round(pred_spread, 3),
                    "edge_spread": None if edge_spread is None else round(edge_spread, 3),
                    "pick_spread": pick_spread,
                    "line_total": line_total,
                    "pred_total": round(pred_total, 3),
                    "edge_total": None if edge_total is None else round(edge_total, 3),
                    "pick_total": pick_total,
                    "result": ",".join(result_parts),
                    "roi": round(roi_units, 3),
                }
            )

            model.update(
                {
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                }
            )

        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "multi_market_predictions.csv"
        self._write_predictions(out_file, predictions)

        self.print_output(
            {
                "games": len(games),
                "predictions_csv": str(out_file),
            },
            format=args.output_format,
        )
        return 0

    def _load_games(self, path: Path, sport: str) -> Iterable[BacktestRow]:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                normalized = normalize_game_row(row, sport=sport)
                line_spread = self._coerce_float(row, ["line_spread", "spread_line", "spread"])
                line_total = self._coerce_float(row, ["line_total", "total_line", "total"])
                yield BacktestRow(
                    home_team=normalized["home_team"],
                    away_team=normalized["away_team"],
                    home_score=float(normalized["home_score"]),
                    away_score=float(normalized["away_score"]),
                    date=str(normalized.get("date", "")),
                    line_spread=line_spread,
                    line_total=line_total,
                )

    def _coerce_float(self, row: Dict[str, Any], keys: List[str]) -> Optional[float]:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return float(value)
        return None

    def _write_predictions(self, path: Path, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    tool = MultiMarketBacktestTool()
    return tool.main()


if __name__ == "__main__":
    raise SystemExit(main())
