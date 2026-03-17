from __future__ import annotations

import pandas as pd

from src.data.datasources import APIDataSource


def test_api_data_source_normalizes_missing_columns(monkeypatch):
    raw = pd.DataFrame(
        {
            "date": ["2024-10-01"],
            "league": ["nba"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_score": [100],
            "away_score": [95],
            "total": [195.5],
        }
    )

    def fake_read_json(_: str) -> pd.DataFrame:
        return raw

    monkeypatch.setattr(pd, "read_json", fake_read_json)

    df = APIDataSource(endpoint="https://example.test/games").load()

    assert df.loc[0, "date"] == pd.Timestamp("2024-10-01")
    assert "closing_total" in df.columns
    assert pd.isna(df.loc[0, "closing_total"])


def test_api_data_source_wraps_list_payload(monkeypatch):
    payload = [
        {
            "date": "2024-10-01",
            "league": "nhl",
            "home_team": "X",
            "away_team": "Y",
            "home_score": 3,
            "away_score": 1,
            "total": 4.5,
        }
    ]

    def fake_read_json(_: str):
        return payload

    monkeypatch.setattr(pd, "read_json", fake_read_json)

    df = APIDataSource(endpoint="https://example.test/games").load()

    assert len(df) == 1
    assert df.loc[0, "league"] == "nhl"
