from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient

from app.utils.security import sign

API_HEADERS = {"X-API-Key": "test-key"}


def _send_webhook(client: TestClient) -> None:
    payload = {
        "source": "joinquant",
        "sent_at": "2025-09-12T17:31:02",
        "positions": [
            {"code": "600519", "weight": 0.2, "price": 1572.5, "qty": 100},
            {"code": "000001", "weight": 0.1, "price": 12.35, "qty": 200},
        ],
        "orders": [],
    }
    timestamp = str(int(time.time()))
    signature = sign(json.dumps(payload, separators=(",", ":")), int(timestamp), "test-secret")
    client.post(
        "/webhook/jq/signal",
        json=payload,
        headers={**API_HEADERS, "X-Signature": signature, "X-Timestamp": timestamp},
    )


def test_positions_current(client: TestClient) -> None:
    _send_webhook(client)
    response = client.get("/positions/current", headers=API_HEADERS)
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["code"] == "600519" for item in items)
