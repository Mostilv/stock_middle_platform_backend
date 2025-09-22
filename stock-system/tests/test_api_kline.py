from __future__ import annotations

from fastapi.testclient import TestClient

API_HEADERS = {"X-API-Key": "test-key"}


def test_kline_endpoint(client: TestClient) -> None:
    client.post("/tasks/refresh-daily", json={"codes": ["600519"]}, headers=API_HEADERS)
    response = client.get(
        "/stocks/600519/kline",
        params={"period": "daily", "adjust": "qfq"},
        headers=API_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bars"], "Kline data should not be empty"
