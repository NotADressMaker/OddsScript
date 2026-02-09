"""Smoke tests for the FastAPI app."""

import pytest


def test_api_health_endpoint():
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import api

    client = TestClient(api.app)
    response = client.get("/")
    assert response.status_code == 200
