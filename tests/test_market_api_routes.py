"""
Integration Test Suite for Person 3: Market ML REST API Layer
Tests health check endpoints, stock listings, and profile routes.
"""

from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_stocks_list():
    response = client.get("/api/stocks")
    assert response.status_code == 200
    stocks = response.json()
    assert isinstance(stocks, list)
    assert len(stocks) > 0


def test_homepage_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Market ML" in response.text
