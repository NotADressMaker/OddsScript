"""Feature engineering routines."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def build_game_team_features(games: Iterable[dict], odds: Iterable[dict], injuries: Iterable[dict], observed_at: str) -> list[dict]:
    features: list[dict] = []
    odds_by_game = defaultdict(list)
    for item in odds:
        odds_by_game[item.get("event_id")].append(item)

    injuries_by_team = defaultdict(list)
    for report in injuries:
        team_id = report.get("team_id") or report.get("team")
        injuries_by_team[team_id].append(report)

    for game in games:
        game_id = game.get("game_id")
        for team_id in [game.get("home_team_id"), game.get("away_team_id")]:
            team_injuries = injuries_by_team.get(team_id, [])
            movement = _line_movement(odds_by_game.get(game_id, []))
            features.append(
                {
                    "game_id": game_id,
                    "team_id": team_id,
                    "observed_at": observed_at,
                    "rest_days": game.get("rest_days"),
                    "back_to_back": game.get("back_to_back"),
                    "rolling_efficiency": game.get("rolling_efficiency"),
                    "closing_line": movement.get("closing_line"),
                    "line_movement": movement.get("line_movement"),
                    "injury_impact": bool(team_injuries),
                }
            )
    return features


def build_game_player_features(games: Iterable[dict], injuries: Iterable[dict], observed_at: str) -> list[dict]:
    features: list[dict] = []
    injuries_by_player = defaultdict(list)
    for report in injuries:
        player_id = report.get("player_id") or report.get("player")
        injuries_by_player[player_id].append(report)

    for game in games:
        game_id = game.get("game_id")
        for player in game.get("players", []):
            player_id = player.get("player_id")
            player_injuries = injuries_by_player.get(player_id, [])
            latest_status = player_injuries[-1].get("status") if player_injuries else None
            features.append(
                {
                    "game_id": game_id,
                    "player_id": player_id,
                    "observed_at": observed_at,
                    "minutes_restriction": any(r.get("minutes_restriction") for r in player_injuries),
                    "injury_status": latest_status,
                    "rolling_usage": player.get("rolling_usage"),
                }
            )
    return features


def _line_movement(odds: Iterable[dict]) -> dict:
    if not odds:
        return {"closing_line": None, "line_movement": None}
    sorted_odds = sorted(odds, key=lambda item: item.get("observed_at") or "")
    opening = sorted_odds[0].get("line")
    closing = sorted_odds[-1].get("line")
    if opening is None or closing is None:
        return {"closing_line": closing, "line_movement": None}
    return {"closing_line": closing, "line_movement": closing - opening}

