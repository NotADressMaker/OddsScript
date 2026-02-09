from __future__ import annotations

import importlib
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _load_app(rate_limit: int = 60, body_limit: int = 1024 * 1024) -> FastAPI:
    import src.api.main as api_main

    os.environ["SBL_RATE_LIMIT_PER_MINUTE"] = str(rate_limit)
    os.environ["SBL_MAX_REQUEST_BYTES"] = str(body_limit)
    api_main = importlib.reload(api_main)
    return api_main.app


def test_localhost_url_blocked() -> None:
    app = _load_app()
    client = TestClient(app)
    response = client.post("/fetch-text", json={"url": "http://127.0.0.1"})
    assert response.status_code == 403


def test_request_body_limit() -> None:
    app = _load_app(body_limit=64)
    client = TestClient(app)
    response = client.post("/health", content=b"x" * 100)
    assert response.status_code == 413


def test_rate_limit() -> None:
    app = _load_app(rate_limit=2)
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    response = client.get("/health")
    assert response.status_code == 429
