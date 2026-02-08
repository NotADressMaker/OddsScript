"""
Basketball totals edge model for NBA/NCAA over/under projections.

Uses a two-stage approach:
1) Project possessions (pace + context adjustments).
2) Project points-per-possession (PPP) using efficiency + matchup deltas.

Designed for dict-like JSON inputs from SportsBetLang ingestion tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import math


LEAGUE_CONFIGS: Dict[str, Dict[str, float]] = {
    "NBA": {
        "league_avg_off_rtg": 114.0,
        "league_avg_def_rtg": 114.0,
        "league_avg_pace": 99.5,
        "league_avg_pace_std": 2.6,
        "league_avg_ftr": 0.210,
        "league_avg_orb_pct": 0.250,
        "league_avg_tov_pct": 0.135,
        "league_avg_three_pa_rate": 0.380,
        "league_avg_rim_rate": 0.310,
        "league_avg_opp_three_pa_allowed_rate": 0.380,
        "league_avg_opp_rim_allowed_rate": 0.310,
        "base_total_sigma": 12.0,
        "min_total_sigma": 8.0,
        "pace_high_threshold": 101.5,
        "pace_low_threshold": 96.0,
        "sigma_high_threshold": 13.0,
        "edge_threshold": 2.0,
        "prob_threshold": 0.55,
        "team_total_gap_threshold": 0.06,
        "b2b_pace_delta": -0.8,
        "altitude_pace_delta": -0.4,
        "travel_pace_delta": -0.3,
        "pace_sigma_floor": 1.0,
        "b2b_poss_sigma": 0.3,
        "altitude_poss_sigma": 0.2,
        "rim_match_weight": 0.18,
        "three_match_weight": 0.16,
        "ftr_weight": 0.30,
        "orb_weight": 0.20,
        "tov_weight": 0.25,
        "pace_sigma_weight": 0.35,
        "three_pa_sigma_weight": 0.60,
        "injury_sigma_weight": 0.80,
    },
    "NCAA": {
        "league_avg_off_rtg": 105.0,
        "league_avg_def_rtg": 105.0,
        "league_avg_pace": 70.0,
        "league_avg_pace_std": 3.2,
        "league_avg_ftr": 0.300,
        "league_avg_orb_pct": 0.300,
        "league_avg_tov_pct": 0.190,
        "league_avg_three_pa_rate": 0.360,
        "league_avg_rim_rate": 0.330,
        "league_avg_opp_three_pa_allowed_rate": 0.360,
        "league_avg_opp_rim_allowed_rate": 0.330,
        "base_total_sigma": 11.0,
        "min_total_sigma": 7.0,
        "pace_high_threshold": 72.0,
        "pace_low_threshold": 66.0,
        "sigma_high_threshold": 12.0,
        "edge_threshold": 1.5,
        "prob_threshold": 0.55,
        "team_total_gap_threshold": 0.06,
        "b2b_pace_delta": -0.6,
        "altitude_pace_delta": -0.3,
        "travel_pace_delta": -0.2,
        "pace_sigma_floor": 1.0,
        "b2b_poss_sigma": 0.25,
        "altitude_poss_sigma": 0.2,
        "rim_match_weight": 0.20,
        "three_match_weight": 0.18,
        "ftr_weight": 0.25,
        "orb_weight": 0.18,
        "tov_weight": 0.20,
        "pace_sigma_weight": 0.32,
        "three_pa_sigma_weight": 0.55,
        "injury_sigma_weight": 0.75,
    },
}


def _merge_config(base: Dict[str, float], override: Optional[Dict[str, Any]]) -> Dict[str, float]:
    merged = dict(base)
    if override:
        for key, value in override.items():
            if isinstance(value, (int, float)):
                merged[key] = float(value)
    return merged


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _prob_over(mean: float, sigma: float, line: float) -> float:
    if sigma <= 0:
        return 0.5
    z = (line - mean) / sigma
    return 1.0 - _normal_cdf(z)


def _window_weight(window_games: Optional[int]) -> float:
    if not window_games:
        return 1.0
    weight = window_games / 10.0
    return min(1.0, max(0.5, weight))


def _extract_players(players_payload: Optional[Any]) -> List[Dict[str, Any]]:
    if not players_payload:
        return []
    if isinstance(players_payload, dict):
        return list(players_payload.get("players", []))
    if isinstance(players_payload, list):
        return list(players_payload)
    return []


def _player_adjustments(players: List[Dict[str, Any]]) -> Tuple[float, float, float, float, List[str]]:
    pace_delta = 0.0
    own_ppp_delta = 0.0
    opp_ppp_delta = 0.0
    variance_boost = 0.0
    tags: List[str] = []

    for player in players:
        status = str(player.get("status", "active")).lower()
        if status not in {"out", "questionable", "doubtful"}:
            continue

        role = str(player.get("role", "")).lower()
        usage = float(player.get("usage", 0.0))
        minutes = float(player.get("minutes", 0.0))
        scale = 1.0
        if usage > 0:
            scale *= min(1.0, usage / 0.25)
        if minutes > 0:
            scale *= min(1.0, minutes / 32.0)
        if status == "questionable":
            scale *= float(player.get("prob_out", 0.5))
        if status == "doubtful":
            scale *= 0.75

        if role == "primary_ballhandler":
            pace_delta -= 0.6 * scale
            own_ppp_delta -= 0.015 * scale
            variance_boost += 0.3 * scale
            tags.append("Key ball-handler out")
        elif role == "rim_protector":
            opp_ppp_delta += 0.02 * scale
            variance_boost += 0.2 * scale
            tags.append("Rim protection weakened")
        else:
            own_ppp_delta -= 0.008 * scale
            variance_boost += 0.1 * scale

    return pace_delta, own_ppp_delta, opp_ppp_delta, variance_boost, tags


def _expected_ppp(
    team: Dict[str, Any],
    opponent: Dict[str, Any],
    config: Dict[str, float],
    tags: List[str],
    variance_tags: List[str],
) -> float:
    league_avg_ppp = config["league_avg_off_rtg"] / 100.0
    off_rtg = float(team.get("off_rtg", config["league_avg_off_rtg"]))
    def_rtg_opp = float(opponent.get("def_rtg", config["league_avg_def_rtg"]))
    off_boost = (off_rtg - config["league_avg_off_rtg"]) / 100.0
    def_weakness = (def_rtg_opp - config["league_avg_def_rtg"]) / 100.0

    rim_rate = float(team.get("rim_rate", config["league_avg_rim_rate"]))
    rim_allowed = float(
        opponent.get("opp_rim_allowed_rate", config["league_avg_opp_rim_allowed_rate"])
    )
    rim_match = (
        (rim_rate - config["league_avg_rim_rate"])
        * (rim_allowed - config["league_avg_opp_rim_allowed_rate"])
        * config["rim_match_weight"]
    )
    if rim_match > 0.005:
        tags.append("Rim pressure edge")

    three_rate = float(team.get("three_pa_rate", config["league_avg_three_pa_rate"]))
    three_allowed = float(
        opponent.get(
            "opp_three_pa_allowed_rate", config["league_avg_opp_three_pa_allowed_rate"]
        )
    )
    three_match = (
        (three_rate - config["league_avg_three_pa_rate"])
        * (three_allowed - config["league_avg_opp_three_pa_allowed_rate"])
        * config["three_match_weight"]
    )
    if three_rate >= config["league_avg_three_pa_rate"] + 0.03:
        variance_tags.append("High 3PA variance")

    ftr = float(team.get("ftr", config["league_avg_ftr"]))
    ftr_adj = (ftr - config["league_avg_ftr"]) * config["ftr_weight"]
    if ftr_adj > 0.01:
        tags.append("FT rate boost")

    orb = float(team.get("orb_pct", config["league_avg_orb_pct"]))
    orb_adj = (orb - config["league_avg_orb_pct"]) * config["orb_weight"]

    tov = float(team.get("tov_pct", config["league_avg_tov_pct"]))
    tov_adj = (config["league_avg_tov_pct"] - tov) * config["tov_weight"]

    ppp = league_avg_ppp + off_boost + def_weakness + rim_match + three_match + ftr_adj + orb_adj + tov_adj
    return max(0.80, ppp)


def pick_best_book(market: Dict[str, Any], side: str = "over") -> Dict[str, Any]:
    """Pick the best line/odds for the specified side from market books."""
    books = list(market.get("books") or [])
    if not books:
        return {
            "book": market.get("book"),
            "total": market.get("total_current") or market.get("total_open"),
            "odds_dec": market.get("odds_over_decimal") if side == "over" else market.get("odds_under_decimal"),
        }

    def book_key(book: Dict[str, Any]) -> Tuple[float, float]:
        total = float(book.get("total", 0.0))
        odds = float(
            book.get("over_odds_dec" if side == "over" else "under_odds_dec", 0.0)
        )
        if side == "over":
            return (total, -odds)
        return (-total, -odds)

    best = sorted(books, key=book_key)[0]
    return {
        "book": best.get("book"),
        "total": best.get("total"),
        "odds_dec": best.get("over_odds_dec" if side == "over" else "under_odds_dec"),
    }


def prob_over(result: Dict[str, Any], line: float) -> float:
    """Convenience helper for SportsBetLang: probability over a line."""
    mean = float(result.get("projected_total", 0.0))
    sigma = float(result.get("total_sigma", 0.0))
    return _prob_over(mean, sigma, float(line))


def compute(
    game: Dict[str, Any],
    home_team_stats: Dict[str, Any],
    away_team_stats: Dict[str, Any],
    market: Optional[Dict[str, Any]] = None,
    home_players: Optional[Any] = None,
    away_players: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute totals projection, probabilities, and betting recommendation."""
    league = str(game.get("league", "NBA")).upper()
    base_config = LEAGUE_CONFIGS.get(league, LEAGUE_CONFIGS["NBA"])
    cfg = _merge_config(base_config, config)

    tags: List[str] = []
    variance_tags: List[str] = []

    home_pace = float(home_team_stats.get("pace", cfg["league_avg_pace"]))
    away_pace = float(away_team_stats.get("pace", cfg["league_avg_pace"]))
    w_home = _window_weight(home_team_stats.get("window_games"))
    w_away = _window_weight(away_team_stats.get("window_games"))
    base_pace = (home_pace * w_home + away_pace * w_away) / (w_home + w_away)

    pace_adjust = 0.0
    if game.get("home_is_b2b"):
        pace_adjust += cfg["b2b_pace_delta"]
        tags.append("B2B fatigue")
    if game.get("away_is_b2b"):
        pace_adjust += cfg["b2b_pace_delta"]
        tags.append("B2B fatigue")
    if game.get("altitude_game"):
        pace_adjust += cfg["altitude_pace_delta"]
        tags.append("Altitude drag")
    if float(game.get("away_travel_km", 0.0)) >= 500.0:
        pace_adjust += cfg["travel_pace_delta"]
        tags.append("Travel fatigue")

    poss_mean = base_pace + pace_adjust
    if poss_mean >= cfg["pace_high_threshold"]:
        tags.append("High pace")

    home_pace_std = float(home_team_stats.get("pace_std", cfg["league_avg_pace_std"]))
    away_pace_std = float(away_team_stats.get("pace_std", cfg["league_avg_pace_std"]))
    poss_sigma = max(cfg["pace_sigma_floor"], (home_pace_std + away_pace_std) / 2.0)
    if game.get("home_is_b2b") or game.get("away_is_b2b"):
        poss_sigma += cfg["b2b_poss_sigma"]
    if game.get("altitude_game"):
        poss_sigma += cfg["altitude_poss_sigma"]

    home_ppp = _expected_ppp(home_team_stats, away_team_stats, cfg, tags, variance_tags)
    away_ppp = _expected_ppp(away_team_stats, home_team_stats, cfg, tags, variance_tags)

    home_players_list = _extract_players(home_players)
    away_players_list = _extract_players(away_players)

    home_pace_delta, home_ppp_delta, home_opp_ppp_delta, home_var, home_tags = _player_adjustments(
        home_players_list
    )
    away_pace_delta, away_ppp_delta, away_opp_ppp_delta, away_var, away_tags = _player_adjustments(
        away_players_list
    )

    tags.extend(home_tags)
    tags.extend(away_tags)

    poss_mean += home_pace_delta + away_pace_delta
    home_ppp += home_ppp_delta + away_opp_ppp_delta
    away_ppp += away_ppp_delta + home_opp_ppp_delta

    projected_total = poss_mean * (home_ppp + away_ppp)

    avg_three_rate = (
        float(home_team_stats.get("three_pa_rate", cfg["league_avg_three_pa_rate"]))
        + float(away_team_stats.get("three_pa_rate", cfg["league_avg_three_pa_rate"]))
    ) / 2.0

    injury_variance = home_var + away_var
    base_sigma = cfg["base_total_sigma"]
    pace_component = poss_sigma * (home_ppp + away_ppp) * cfg["pace_sigma_weight"]
    shot_component = avg_three_rate * cfg["three_pa_sigma_weight"] * base_sigma
    injury_component = injury_variance * cfg["injury_sigma_weight"] * base_sigma
    total_sigma = math.sqrt(base_sigma**2 + pace_component**2 + shot_component**2 + injury_component**2)
    total_sigma = max(cfg["min_total_sigma"], total_sigma)

    if avg_three_rate >= cfg["league_avg_three_pa_rate"] + 0.03:
        variance_tags.append("High 3PA variance")

    line_total = None
    if market:
        line_total = market.get("total_current") or market.get("total_open")
    if line_total is None:
        line_total = projected_total

    prob_over_val = _prob_over(projected_total, total_sigma, float(line_total))
    prob_under_val = 1.0 - prob_over_val
    edge_points = projected_total - float(line_total)

    recommendation = "PASS"
    if edge_points >= cfg["edge_threshold"] and prob_over_val >= cfg["prob_threshold"]:
        recommendation = "OVER"
    elif edge_points <= -cfg["edge_threshold"] and prob_under_val >= cfg["prob_threshold"]:
        recommendation = "UNDER"

    derivative_recommendations: List[str] = []
    league_avg_ppp = cfg["league_avg_off_rtg"] / 100.0
    if poss_mean <= cfg["pace_low_threshold"] and home_ppp < league_avg_ppp and away_ppp < league_avg_ppp:
        derivative_recommendations.append("1H Under candidate")
        tags.append("1H Under candidate")
    if poss_mean >= cfg["pace_high_threshold"] and total_sigma >= cfg["sigma_high_threshold"]:
        derivative_recommendations.append("1Q Over candidate")
        tags.append("1Q Over candidate")
    if abs(home_ppp - away_ppp) >= cfg["team_total_gap_threshold"]:
        if home_ppp > away_ppp:
            derivative_recommendations.append("Home Team Total Over candidate")
            tags.append("Team Total Over candidate")
        else:
            derivative_recommendations.append("Away Team Total Over candidate")
            tags.append("Team Total Over candidate")

    derivative_recommendation = "; ".join(derivative_recommendations) if derivative_recommendations else None
    if recommendation == "PASS" and derivative_recommendation:
        recommendation = "DERIVATIVE"

    chosen_line = None
    chosen_odds = None
    chosen_book = None
    if market and recommendation in {"OVER", "UNDER"}:
        best = pick_best_book(market, side="over" if recommendation == "OVER" else "under")
        chosen_line = best.get("total")
        chosen_odds = best.get("odds_dec")
        chosen_book = best.get("book")
    elif market:
        chosen_line = line_total
        chosen_odds = market.get("odds_over_decimal") if edge_points >= 0 else market.get("odds_under_decimal")
        chosen_book = market.get("book")

    if market:
        bets_pct_over = market.get("bets_pct_over")
        money_pct_over = market.get("money_pct_over")
        total_open = market.get("total_open")
        total_current = market.get("total_current")
        if (
            isinstance(bets_pct_over, (int, float))
            and isinstance(total_open, (int, float))
            and isinstance(total_current, (int, float))
        ):
            if bets_pct_over >= 0.65 and total_current < total_open:
                tags.append("Sharp total move (under lean)")
            if bets_pct_over <= 0.35 and total_current > total_open:
                tags.append("Sharp total move (over lean)")
        if isinstance(money_pct_over, (int, float)) and money_pct_over < 0.45:
            tags.append("Money leaning under")

    tags.extend(variance_tags)

    return {
        "projected_total": projected_total,
        "total_sigma": total_sigma,
        "edge_points": edge_points,
        "prob_over": prob_over_val,
        "prob_under": prob_under_val,
        "poss_mean": poss_mean,
        "home_ppp": home_ppp,
        "away_ppp": away_ppp,
        "recommendation": recommendation,
        "derivative_recommendation": derivative_recommendation,
        "chosen_line": chosen_line,
        "chosen_odds_dec": chosen_odds,
        "chosen_book": chosen_book,
        "tags": sorted(set(tags)),
    }
