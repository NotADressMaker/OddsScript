import math

from lib.elo_totals import EloTotalsModel


def test_update_determinism():
    model_a = EloTotalsModel(league="NBA", k_factor=20.0)
    model_b = EloTotalsModel(league="NBA", k_factor=20.0)
    game = {"home_team": "A", "away_team": "B", "home_score": 110, "away_score": 100}

    model_a.update(game)
    model_b.update(game)

    team_a_a = model_a.get_or_create_team("A")
    team_a_b = model_b.get_or_create_team("A")
    team_b_a = model_a.get_or_create_team("B")
    team_b_b = model_b.get_or_create_team("B")

    assert math.isclose(team_a_a.offense, team_a_b.offense)
    assert math.isclose(team_a_a.defense, team_a_b.defense)
    assert math.isclose(team_b_a.offense, team_b_b.offense)
    assert math.isclose(team_b_a.defense, team_b_b.defense)


def test_prediction_sanity_offense_defense():
    model = EloTotalsModel(league="NBA")
    home = model.get_or_create_team("Home")
    away = model.get_or_create_team("Away")

    baseline = model.predict_total("Home", "Away")
    home.offense += 100
    higher_offense = model.predict_total("Home", "Away")
    assert higher_offense > baseline

    away.defense += 100
    stronger_defense = model.predict_total("Home", "Away")
    assert stronger_defense < higher_offense


def test_prob_over_bounds():
    model = EloTotalsModel(league="NBA")
    prob = model.prob_over("A", "B", 220.0)
    assert 0.0 <= prob <= 1.0


def test_unseen_team_fallback():
    model = EloTotalsModel(league="NBA")
    total = model.predict_total("Unknown1", "Unknown2")
    assert total > 0
