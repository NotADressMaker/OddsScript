import pandas as pd

from sportsbetlang.horse_racing_derby import DerbyValueBetPipeline


def _sample_data():
    return pd.DataFrame(
        [
            {"horse": "A", "jockey": "J1", "trainer": "T1", "finish_position": 1, "speed_figure": 98, "distance_furlongs": 10, "track_condition": "fast", "market_odds_decimal": 3.2, "race_date": "2024-04-01"},
            {"horse": "B", "jockey": "J2", "trainer": "T2", "finish_position": 2, "speed_figure": 94, "distance_furlongs": 10, "track_condition": "fast", "market_odds_decimal": 4.5, "race_date": "2024-04-01"},
            {"horse": "A", "jockey": "J1", "trainer": "T1", "finish_position": 2, "speed_figure": 96, "distance_furlongs": 10, "track_condition": "good", "market_odds_decimal": 3.6, "race_date": "2024-05-01"},
            {"horse": "B", "jockey": "J2", "trainer": "T2", "finish_position": 1, "speed_figure": 99, "distance_furlongs": 10, "track_condition": "good", "market_odds_decimal": 3.9, "race_date": "2024-05-01"},
            {"horse": "A", "jockey": "J1", "trainer": "T1", "finish_position": 1, "speed_figure": 101, "distance_furlongs": 10, "track_condition": "fast", "market_odds_decimal": 3.0, "race_date": "2025-05-03"},
            {"horse": "B", "jockey": "J2", "trainer": "T2", "finish_position": 2, "speed_figure": 95, "distance_furlongs": 10, "track_condition": "sloppy", "market_odds_decimal": 5.2, "race_date": "2025-05-03"},
        ]
    )


def test_derby_pipeline_outputs_true_odds_and_value_flags():
    pipeline = DerbyValueBetPipeline()
    output = pipeline.run_from_dataframe(_sample_data(), cutoff_date="2025-01-01")

    assert not output.scored_runners.empty
    assert "true_decimal_odds" in output.scored_runners.columns
    assert "is_value_bet" in output.scored_runners.columns
    assert "brier" in output.metrics
    assert output.value_bet_summary["count"].iloc[0] >= 0
