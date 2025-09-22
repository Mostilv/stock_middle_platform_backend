from __future__ import annotations

from fastapi.testclient import TestClient

API_HEADERS = {"X-API-Key": "test-key"}


def test_indicator_computation(client: TestClient) -> None:
    refresh = client.post("/tasks/refresh-daily", json={"codes": ["600519"]}, headers=API_HEADERS)
    assert refresh.status_code == 200
    compute = client.post(
        "/tasks/compute-indicators",
        json={"codes": ["600519"], "indicators": ["MA", "RSI"]},
        headers=API_HEADERS,
    )
    assert compute.status_code == 200
    technicals = client.get(
        "/stocks/600519/technicals",
        params={"names": "MA,RSI"},
        headers=API_HEADERS,
    )
    assert technicals.status_code == 200
    body = technicals.json()
    ma_series = next(item for item in body["indicators"] if item["name"] == "MA")
    assert ma_series["series"], "MA series should not be empty"
