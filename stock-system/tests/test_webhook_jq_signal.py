from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient

from app.utils.security import sign

API_HEADERS = {"X-API-Key": "test-key"}


def test_webhook_signal_flow(client: TestClient) -> None:
    payload = {
        "source": "joinquant",
        "sent_at": "2025-09-12T17:31:02",
        "positions": [
            {"code": "600519", "weight": 0.2, "price": 1572.5, "qty": 100},
            {"code": "000001", "weight": 0.1, "price": 12.35, "qty": 200},
        ],
        "orders": [
            {
                "code": "600519",
                "side": "BUY",
                "qty": 100,
                "price": 1570.0,
                "reason": "rebalance",
            },
            {
                "code": "000001",
                "side": "SELL",
                "qty": 200,
                "price": 12.30,
                "reason": "stop",
            },
        ],
        "note": "daily close rebalance",
    }
    timestamp = str(int(time.time()))
    signature = sign(json.dumps(payload, separators=(",", ":")), int(timestamp), "test-secret")
    response = client.post(
        "/webhook/jq/signal",
        json=payload,
        headers={
            **API_HEADERS,
            "X-Signature": signature,
            "X-Timestamp": timestamp,
        },
    )
    assert response.status_code == 200
    signals_resp = client.get("/signals/recent", headers=API_HEADERS)
    assert signals_resp.status_code == 200
    assert signals_resp.json()["items"], "Signals should be recorded"
