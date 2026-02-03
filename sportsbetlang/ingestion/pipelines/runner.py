"""Pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sportsbetlang.ingestion.config import PipelineConfig, PipelineReport, RunContext, Tooling
from sportsbetlang.ingestion.db.client import DatabaseClient
from sportsbetlang.ingestion.extractors.injury_extractor import extract_injuries
from sportsbetlang.ingestion.features.builder import build_game_player_features, build_game_team_features
from sportsbetlang.ingestion.normalizers.entities import resolve_player_id, resolve_team_id
from sportsbetlang.ingestion.schemas import registry
from sportsbetlang.ingestion.sources.game_data import fetch_game_data
from sportsbetlang.ingestion.sources.injuries import fetch_injuries
from sportsbetlang.ingestion.sources.odds import fetch_odds


@dataclass
class PipelineRunner:
    tooling: Tooling

    def run(self, config: PipelineConfig, mode: str) -> PipelineReport:
        observed_at = self.tooling.now_utc()
        context = RunContext(observed_at=observed_at, run_mode=mode)
        db = DatabaseClient(self.tooling.query_db, self.tooling.upsert_db)

        date_range = {"start_date": config.start_date, "end_date": config.end_date}

        games = fetch_game_data(self.tooling.get_game_data, config.sport, date_range, level="scores")
        if not games:
            context.record_gap(_gap("games", "empty_payload", observed_at))
        normalized_games = self._normalize_games(games, observed_at)
        db.upsert("games", normalized_games, conflict_keys=["game_id"])

        odds_snapshots = fetch_odds(
            self.tooling.get_odds,
            config.sport,
            config.market_list(),
            date_range,
            observed_at,
        )
        if not odds_snapshots:
            context.record_gap(_gap("odds", "empty_payload", observed_at))
        odds_schema = registry.load_schema("odds_snapshot.json")
        valid_odds = self._validate_records(odds_snapshots, odds_schema, "odds")
        db.upsert("odds_snapshots", valid_odds, conflict_keys=["book", "market", "selection", "event_id", "observed_at"])

        raw_injuries = fetch_injuries(self.tooling.get_injuries, config.sport, date_range)
        if raw_injuries in (None, [], {}):
            context.record_gap(_gap("injuries", "empty_payload", observed_at))
        extraction = extract_injuries(raw_injuries, observed_at, source="get_injuries")
        for gap in extraction.data_gaps:
            context.record_gap(gap)
        injury_schema = registry.load_schema("injury_report.json")
        valid_injuries = self._validate_records(extraction.records, injury_schema, "injuries")
        enriched_injuries = self._resolve_injury_entities(valid_injuries, config.sport)
        db.upsert("injury_reports", enriched_injuries, conflict_keys=["player_id", "observed_at", "source"])

        team_features = build_game_team_features(normalized_games, valid_odds, enriched_injuries, observed_at)
        player_features = build_game_player_features(normalized_games, enriched_injuries, observed_at)
        db.upsert("features_game_team", team_features, conflict_keys=["game_id", "team_id", "observed_at"])
        db.upsert("features_game_player", player_features, conflict_keys=["game_id", "player_id", "observed_at"])

        counts = {
            "games": len(normalized_games),
            "odds": len(valid_odds),
            "injuries": len(enriched_injuries),
            "features_game_team": len(team_features),
            "features_game_player": len(player_features),
        }
        preview_sql = (
            "SELECT * FROM features_game_team WHERE observed_at::date = %(date)s "
            "ORDER BY game_id, team_id"
        )
        return PipelineReport(counts=counts, data_gaps=context.data_gaps, feature_preview_sql=preview_sql)

    def _normalize_games(self, games: Iterable[dict], observed_at: str) -> list[dict]:
        normalized: list[dict] = []
        for game in games:
            home_name = game.get("home_team") or game.get("home_team_name")
            away_name = game.get("away_team") or game.get("away_team_name")
            league = game.get("league")
            home_id = resolve_team_id(home_name, league) if home_name else None
            away_id = resolve_team_id(away_name, league) if away_name else None
            normalized.append(
                {
                    "game_id": str(game.get("game_id") or game.get("event_id")),
                    "league": league,
                    "sport": game.get("sport"),
                    "start_time": game.get("start_time"),
                    "home_team_id": home_id,
                    "away_team_id": away_id,
                    "source": game.get("source", "get_game_data"),
                    "created_at": observed_at,
                    "players": game.get("players", []),
                    "rest_days": game.get("rest_days"),
                    "back_to_back": game.get("back_to_back"),
                    "rolling_efficiency": game.get("rolling_efficiency"),
                }
            )
        return normalized

    def _resolve_injury_entities(self, injuries: Iterable[dict], league: str) -> list[dict]:
        enriched: list[dict] = []
        for report in injuries:
            team_name = report.get("team")
            team_id = resolve_team_id(team_name, league) if team_name else None
            player_name = report.get("player")
            player_id = resolve_player_id(player_name, team_id) if player_name else None
            enriched.append({**report, "team_id": team_id, "player_id": player_id, "league": report.get("league") or league})
        return enriched

    def _validate_records(self, records: Iterable[dict], schema: dict, category: str) -> list[dict]:
        valid: list[dict] = []
        for record in records:
            tool_result = self.tooling.validate_schema(record, schema.get("title", category))
            if isinstance(tool_result, dict) and tool_result.get("ok"):
                valid.append(record)
                continue
            ok, errors = registry.validate_basic(schema, record)
            if ok:
                valid.append(record)
        return valid


def _gap(category: str, reason: str, observed_at: str) -> dict:
    return {"category": category, "reason": reason, "observed_at": observed_at}
