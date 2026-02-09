"""FastAPI service for totals predictions."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Awaitable, Callable, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import Response

from sportsbetlang.api.safe_http import fetch_text
from src.models.inference import load_bundle, predict_totals
from src.utils.config import LeagueConfig

app = FastAPI(title="Totals Regression API")

REQUEST_BODY_LIMIT = int(os.getenv("SBL_MAX_REQUEST_BYTES", "1048576"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("SBL_RATE_LIMIT_PER_MINUTE", "60"))
_RATE_LIMIT_WINDOW_S = 60.0
_rate_limit_state: dict[str, tuple[float, int]] = {}


def _load_allowed_domains() -> Optional[set[str]]:
    raw = os.getenv("SBL_ALLOWED_DOMAINS", "")
    domains = {entry.strip().lower() for entry in raw.split(",") if entry.strip()}
    return domains or None


@app.middleware("http")
async def request_body_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > REQUEST_BODY_LIMIT:
            return JSONResponse(status_code=413, content={"detail": "Request body too large."})
        body = await request.body()
        if len(body) > REQUEST_BODY_LIMIT:
            return JSONResponse(status_code=413, content={"detail": "Request body too large."})
        request._body = body
    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    client_host = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window_start, count = _rate_limit_state.get(client_host, (now, 0))
    if now - window_start >= _RATE_LIMIT_WINDOW_S:
        window_start = now
        count = 0
    if count >= RATE_LIMIT_PER_MINUTE:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded."})
    _rate_limit_state[client_host] = (window_start, count + 1)
    if len(_rate_limit_state) > 1000:
        cutoff = now - _RATE_LIMIT_WINDOW_S
        for host, (start, _) in list(_rate_limit_state.items()):
            if start < cutoff:
                _rate_limit_state.pop(host, None)
    return await call_next(request)


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


class FetchTextRequest(BaseModel):
    url: str
    timeout_s: float = Field(5.0, ge=0.1, le=30.0)
    max_bytes: int = Field(200_000, ge=1, le=1_000_000)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/fetch-text")
async def fetch_text_endpoint(request: FetchTextRequest) -> dict[str, str]:
    allowed_domains = _load_allowed_domains()
    content = await fetch_text(
        request.url,
        timeout_s=request.timeout_s,
        max_bytes=request.max_bytes,
        allowed_domains=allowed_domains,
    )
    return {"content": content}


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
