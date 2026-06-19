from sportsbetlang.data.ufc_dataset import american_implied_probability, build_ufc_fight_dataset


def test_american_implied_probability_for_favorites_and_underdogs():
    assert american_implied_probability(-150) == 0.6
    assert american_implied_probability(200) == 0.333333


def test_build_ufc_fight_dataset_normalizes_aliases():
    rows = build_ufc_fight_dataset([
        {
            "date": "2026-06-20",
            "event": "UFC Test",
            "division": "Welterweight",
            "fighter_name": "Alpha",
            "opponent_name": "Beta",
            "odds": "-125",
            "outcome": "win",
            "finish_round": "2",
        }
    ])

    assert rows == [
        {
            "event_date": "2026-06-20",
            "event_name": "UFC Test",
            "weight_class": "Welterweight",
            "fighter": "Alpha",
            "opponent": "Beta",
            "is_favorite": "",
            "moneyline": -125,
            "implied_probability": 0.555556,
            "result": "win",
            "method": "",
            "round": 2,
            "scheduled_rounds": "",
            "reach_inches": "",
            "height_inches": "",
            "age": "",
            "sig_strikes_landed": "",
            "sig_strikes_attempted": "",
            "takedowns_landed": "",
            "takedowns_attempted": "",
            "sub_attempts": "",
        }
    ]
