"""FastAPI service for totals predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.models.inference import load_bundle, predict_totals
from src.utils.config import LeagueConfig

app = FastAPI(title="Totals Regression API")


class PredictionRequest(BaseModel):
    league: str = Field(..., example="NBA")
    home_team: str
    away_team: str
    date: str
    line: Optional[float] = None


class PredictionResponse(BaseModel):
    predicted_total_mean: float
    prediction_interval_80_low: float
    prediction_interval_80_high: float
    probability_over: Optional[float] = None
    warning: Optional[str] = None


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    config_path = Path("configs") / f"{request.league.lower()}.yaml"
    artifact_dir = Path("artifacts") / request.league / "latest"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="League config not found.")
    if not artifact_dir.exists():
        raise HTTPException(status_code=404, detail="Model artifacts not found.")

    config = LeagueConfig.from_yaml(config_path)
    historical_path = Path("data") / f"{request.league.lower()}_historical.csv"
    if not historical_path.exists():
        raise HTTPException(status_code=404, detail="Historical data not found.")

    historical = pd.read_csv(historical_path)
    if historical.empty:
        raise HTTPException(status_code=400, detail="Historical data is empty.")

    upcoming = pd.DataFrame(
        [
            {
                "date": request.date,
                "league": request.league,
                "home_team": request.home_team,
                "away_team": request.away_team,
            }
        ]
    )
    for col in historical.columns:
        if col not in upcoming.columns:
            upcoming[col] = pd.NA
    upcoming = upcoming[historical.columns]
    upcoming["date"] = pd.to_datetime(upcoming["date"], errors="coerce")

    bundle = load_bundle(artifact_dir)
    predictions = predict_totals(
        historical_df=historical,
        upcoming_df=upcoming,
        rolling_window=config.rolling_window,
        bundle=bundle,
        line=request.line,
    )

    row = predictions.iloc[0]
    return PredictionResponse(
        predicted_total_mean=float(row["predicted_total_mean"]),
        prediction_interval_80_low=float(row["prediction_interval_80_low"]),
        prediction_interval_80_high=float(row["prediction_interval_80_high"]),
        probability_over=float(row["probability_over"]) if "probability_over" in row else None,
        warning=str(row["warning"]) if "warning" in row and pd.notna(row["warning"]) else None,
    )
