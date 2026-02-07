from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from src.models.training import train_models


def test_api_prediction_response(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    configs_dir.joinpath("nba.yaml").write_text(
        "league: NBA\nrolling_window: 2\ntest_size: 2\nquantile_low: 0.1\nquantile_high: 0.9\n"
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    historical = pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-05",
                "2024-01-10",
                "2024-01-15",
            ],
            "league": ["NBA", "NBA", "NBA", "NBA"],
            "home_team": ["A", "B", "A", "B"],
            "away_team": ["B", "A", "B", "A"],
            "home_score": [100, 95, 110, 90],
            "away_score": [90, 105, 98, 102],
            "total": [190, 200, 208, 192],
        }
    )
    historical.to_csv(data_dir / "nba_historical.csv", index=False)

    features = pd.DataFrame(
        {
            "home_roll_points_for": [100, 95, 110, 90],
            "away_roll_points_for": [90, 105, 98, 102],
        }
    )
    target = pd.Series([190, 200, 208, 192])

    artifact_dir = tmp_path / "artifacts" / "NBA" / "latest"
    train_models(
        features=features,
        target=target,
        output_dir=artifact_dir,
        config={
            "league": "NBA",
            "rolling_window": 2,
            "test_size": 2,
            "quantile_low": 0.1,
            "quantile_high": 0.9,
        },
    )

    from src.api.main import app

    client = TestClient(app)
    response = client.post(
        "/predict",
        json={
            "league": "NBA",
            "home_team": "A",
            "away_team": "B",
            "date": "2024-02-01",
            "line": 200.5,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "predicted_total_mean" in payload
    assert "prediction_interval_80_low" in payload
    assert "prediction_interval_80_high" in payload
