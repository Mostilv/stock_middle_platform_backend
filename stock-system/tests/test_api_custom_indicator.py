from __future__ import annotations

from fastapi.testclient import TestClient

API_HEADERS = {"X-API-Key": "test-key"}


def test_custom_indicator_cycle(client: TestClient) -> None:
    client.post("/tasks/refresh-daily", json={"codes": ["600519"]}, headers=API_HEADERS)
    define_resp = client.post(
        "/indicators/custom/define",
        json={
            "name": "MY_MOM",
            "description": "自定义动量指标",
            "params_schema": {"period": {"type": "int", "min": 1, "default": 20}},
            "impl_ref": "app.indicators.custom.momentum_v1.MomentumV1",
        },
        headers=API_HEADERS,
    )
    assert define_resp.status_code == 200
    compute_resp = client.post(
        "/indicators/custom/compute",
        json={
            "codes": ["600519"],
            "indicator": "MY_MOM",
            "params": {"period": 5},
            "start": None,
            "end": None,
            "async": False,
        },
        headers=API_HEADERS,
    )
    assert compute_resp.status_code == 200
    query_resp = client.get(
        "/indicators/custom/query",
        params={"code": "600519", "indicator": "MY_MOM"},
        headers=API_HEADERS,
    )
    assert query_resp.status_code == 200
    body = query_resp.json()
    assert body["series"], "Custom indicator series should not be empty"
