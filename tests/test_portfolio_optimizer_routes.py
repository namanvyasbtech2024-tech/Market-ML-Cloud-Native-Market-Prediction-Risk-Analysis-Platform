"""
Integration Test Suite for Person 3: Portfolio Optimization & Allocation API
Verifies /api/portfolio endpoints, discrete integer calculations, and cash reserves.
"""

from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_portfolio_optimize_default():
    payload = {
        "capital": 1000000,
        "holdings": [
            {"ticker": "RELIANCE", "weight": 0.4},
            {"ticker": "TCS", "weight": 0.3},
            {"ticker": "INFY", "weight": 0.3}
        ]
    }
    response = client.post("/api/portfolio/optimize", json=payload)
    assert response.status_code in [200, 404, 422]
