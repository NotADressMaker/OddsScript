"""Utilities for identifying relevant ATS (against-the-spread) trends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


@dataclass(frozen=True)
class ATSGameResult:
    """Single game ATS outcome for a team."""

    team: str
    opponent: str
    sport: str
    is_home: bool
    was_favorite: bool
    spread: float
    team_score: int
    opponent_score: int

    @property
    def margin(self) -> int:
        """Team scoring margin (team - opponent)."""
        return self.team_score - self.opponent_score

    @property
    def ats_margin(self) -> float:
        """Margin against the closing spread; positive values indicate a cover."""
        return self.margin + self.spread


@dataclass(frozen=True)
class ATSRecord:
    """ATS record summary."""

    wins: int
    losses: int
    pushes: int

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.pushes

    @property
    def cover_rate(self) -> float:
        graded_games = self.wins + self.losses
        if graded_games == 0:
            return 0.0
        return self.wins / graded_games


@dataclass(frozen=True)
class ATSTrendInsight:
    """Describes a relevant trend detected from ATS results."""

    title: str
    sample_size: int
    record: ATSRecord
    strength: Literal["strong", "moderate"]


def _result_from_game(game: ATSGameResult) -> Literal["win", "loss", "push"]:
    if game.ats_margin > 0:
        return "win"
    if game.ats_margin < 0:
        return "loss"
    return "push"


def calculate_ats_record(games: Iterable[ATSGameResult]) -> ATSRecord:
    """Calculate ATS wins/losses/pushes from game results."""
    wins = 0
    losses = 0
    pushes = 0

    for game in games:
        result = _result_from_game(game)
        if result == "win":
            wins += 1
        elif result == "loss":
            losses += 1
        else:
            pushes += 1

    return ATSRecord(wins=wins, losses=losses, pushes=pushes)


def current_ats_streak(games: list[ATSGameResult]) -> tuple[str, int]:
    """
    Return current ATS streak for chronological games.

    Returns:
        (streak_type, streak_length)
        streak_type is one of: "covers", "non-covers", "none"
    """
    if not games:
        return "none", 0

    streak_type = "none"
    streak_length = 0

    for game in reversed(games):
        result = _result_from_game(game)
        if result == "push":
            continue

        current_type = "covers" if result == "win" else "non-covers"
        if streak_type == "none":
            streak_type = current_type
            streak_length = 1
            continue

        if current_type == streak_type:
            streak_length += 1
        else:
            break

    if streak_type == "none":
        return "none", 0

    return streak_type, streak_length


def find_relevant_ats_trends(
    games: Iterable[ATSGameResult],
    *,
    min_games: int = 8,
    moderate_cover_rate: float = 0.58,
    strong_cover_rate: float = 0.65,
) -> list[ATSTrendInsight]:
    """
    Identify relevant ATS trends for a professional team.

    Trends are evaluated across common handicapping splits:
    overall, home, away, favorite, and underdog.
    """
    games_list = list(games)

    if min_games <= 0:
        raise ValueError("min_games must be positive")
    if not 0.5 < moderate_cover_rate <= strong_cover_rate <= 1:
        raise ValueError("cover rate thresholds must satisfy 0.5 < moderate <= strong <= 1")

    segments = {
        "Overall ATS": games_list,
        "Home ATS": [game for game in games_list if game.is_home],
        "Away ATS": [game for game in games_list if not game.is_home],
        "As Favorite ATS": [game for game in games_list if game.was_favorite],
        "As Underdog ATS": [game for game in games_list if not game.was_favorite],
    }

    insights: list[ATSTrendInsight] = []

    for title, segment_games in segments.items():
        if len(segment_games) < min_games:
            continue

        record = calculate_ats_record(segment_games)
        rate = record.cover_rate
        if rate >= strong_cover_rate:
            strength = "strong"
        elif rate >= moderate_cover_rate:
            strength = "moderate"
        elif (1 - rate) >= strong_cover_rate:
            strength = "strong"
        elif (1 - rate) >= moderate_cover_rate:
            strength = "moderate"
        else:
            continue

        insights.append(
            ATSTrendInsight(
                title=title,
                sample_size=record.games,
                record=record,
                strength=strength,
            )
        )

    return insights
