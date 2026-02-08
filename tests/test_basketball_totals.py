import math

from lib import basketball_totals


def base_inputs():
    game = {
        "game_id": "NBA_2026_02_07_LAL_BOS",
        "league": "NBA",
        "neutral_site": False,
        "home_is_b2b": False,
        "away_is_b2b": False,
        "away_travel_km": 0,
        "altitude_game": False,
    }
    home = {
        "team": "BOS",
        "pace": 100.0,
        "pace_std": 2.5,
        "off_rtg": 118.0,
        "def_rtg": 112.0,
        "tov_pct": 0.13,
        "orb_pct": 0.26,
        "ftr": 0.22,
        "three_pa_rate": 0.38,
        "rim_rate": 0.32,
        "opp_three_pa_allowed_rate": 0.38,
        "opp_rim_allowed_rate": 0.32,
        "window_games": 10,
    }
    away = {
        "team": "LAL",
        "pace": 100.0,
        "pace_std": 2.5,
        "off_rtg": 114.0,
        "def_rtg": 114.0,
        "tov_pct": 0.14,
        "orb_pct": 0.25,
        "ftr": 0.21,
        "three_pa_rate": 0.36,
        "rim_rate": 0.31,
        "opp_three_pa_allowed_rate": 0.37,
        "opp_rim_allowed_rate": 0.31,
        "window_games": 10,
    }
    market = {
        "total_open": 228.5,
        "total_current": 228.5,
        "odds_over_decimal": 1.91,
        "odds_under_decimal": 1.91,
        "books": [
            {"book": "BookA", "total": 228.5, "over_odds_dec": 1.91, "under_odds_dec": 1.91}
        ],
    }
    return game, home, away, market


def test_deterministic_output():
    game, home, away, market = base_inputs()
    result_a = basketball_totals.compute(game, home, away, market)
    result_b = basketball_totals.compute(game, home, away, market)

    assert math.isclose(result_a["projected_total"], result_b["projected_total"])
    assert math.isclose(result_a["total_sigma"], result_b["total_sigma"])


def test_pace_increases_total():
    game, home, away, market = base_inputs()
    base = basketball_totals.compute(game, home, away, market)
    home_fast = dict(home)
    home_fast["pace"] = 105.0
    faster = basketball_totals.compute(game, home_fast, away, market)
    assert faster["projected_total"] > base["projected_total"]


def test_missing_rim_protector_increases_total():
    game, home, away, market = base_inputs()
    base = basketball_totals.compute(game, home, away, market)
    home_players = {
        "team": "BOS",
        "players": [
            {"name": "C", "status": "out", "role": "rim_protector", "usage": 0.18, "minutes": 28}
        ],
    }
    bumped = basketball_totals.compute(game, home, away, market, home_players=home_players)
    assert bumped["projected_total"] > base["projected_total"]
    assert bumped["away_ppp"] > base["away_ppp"]


def test_three_point_variance_increases_sigma():
    game, home, away, market = base_inputs()
    base = basketball_totals.compute(game, home, away, market)
    home_bombs = dict(home)
    home_bombs["three_pa_rate"] = 0.48
    high_var = basketball_totals.compute(game, home_bombs, away, market)
    assert high_var["total_sigma"] >= base["total_sigma"]


def test_prob_over_bounds():
    game, home, away, market = base_inputs()
    result = basketball_totals.compute(game, home, away, market)
    assert 0.0 <= result["prob_over"] <= 1.0
    assert 0.0 <= result["prob_under"] <= 1.0


def test_missing_optional_inputs():
    game, home, away, _market = base_inputs()
    result = basketball_totals.compute(game, home, away)
    assert result["recommendation"] in {"OVER", "UNDER", "PASS", "DERIVATIVE"}
