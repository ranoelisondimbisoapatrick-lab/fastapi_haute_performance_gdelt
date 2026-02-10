"""
tests/test_health.py

Basic smoke test for the service health endpoint.

Why:
- Ensures the FastAPI app boots correctly.
- Validates the `/health` contract used by monitoring/CI pipelines.

Run:
  pytest -q
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def client() -> TestClient:
    """Create a TestClient for the FastAPI app.

    Notes:
        - We keep this as a small helper to avoid repeating TestClient(app)
          across multiple tests.
        - If you later add startup/shutdown dependencies, consider using a pytest
          fixture with `yield` and FastAPI lifespan management.
    """
    return TestClient(app)


def test_health_returns_ok() -> None:
    """`GET /health` returns HTTP 200 and a JSON payload with status='ok'."""
    c = client()

    resp = c.get("/health")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    # Optional: keep this if you want to ensure environment is returned.
    assert "env" in payload
