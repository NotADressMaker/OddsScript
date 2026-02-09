import math

from lib.multi_market_ratings import MultiMarketRatingsModel


def test_update_determinism():
    model_a = MultiMarketRatingsModel("NBA")
    model_b = MultiMarketRatingsModel("NBA")
    game = {"home_team": "A", "away_team": "B", "home_score": 120, "away_score": 110}

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


def test_scoring_increase_raises_total():
    model = MultiMarketRatingsModel("NBA")
    baseline = model.predict_total("Home", "Away")

    game = {"home_team": "Home", "away_team": "Away", "home_score": 135, "away_score": 110}
    model.update(game)

    updated_total = model.predict_total("Home", "Away")
    assert updated_total > baseline


def test_defense_improvement_lowers_opponent_score():
    model = MultiMarketRatingsModel("NBA")
    baseline = model.predict("Home", "Away")

    game = {"home_team": "Home", "away_team": "Away", "home_score": 105, "away_score": 85}
    model.update(game)

    updated = model.predict("Home", "Away")
    assert updated["away_score"] < baseline["away_score"]
    assert updated["total"] < baseline["total"]


def test_probability_bounds():
    model = MultiMarketRatingsModel("NFL")
    cover = model.prob_cover("Home", "Away", -3.0)
    over = model.prob_over("Home", "Away", 44.5)
    assert 0.0 <= cover <= 1.0
    assert 0.0 <= over <= 1.0


def test_prob_over_monotonic_with_line():
    model = MultiMarketRatingsModel("NFL")
    lower_line = model.prob_over("Home", "Away", 41.0)
    higher_line = model.prob_over("Home", "Away", 47.0)
    assert lower_line >= higher_line


def test_prob_cover_monotonic_with_line():
    model = MultiMarketRatingsModel("NFL")
    easier = model.prob_cover("Home", "Away", -6.0)
    harder = model.prob_cover("Home", "Away", -2.0)
    assert easier >= harder


def test_sport_configs_supported():
    for sport in ["NBA", "NFL", "NHL", "MLB"]:
        model = MultiMarketRatingsModel(sport)
        assert model.sport == sport
