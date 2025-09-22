from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from ..config import get_settings
from ..repo.mysql import positions_repo, signals_repo
from ..utils.security import verify


class JQBridgeService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def process_webhook(
        self,
        session: Any,
        payload: Dict[str, Any],
        signature: str,
        timestamp: str,
    ) -> Dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":"))
        if not verify(signature, body, timestamp, self.settings.secret_key):
            raise ValueError("Invalid signature")
        as_of = datetime.fromisoformat(payload.get("sent_at")) if payload.get("sent_at") else datetime.utcnow()
        positions = [
            {
                "code": item["code"],
                "qty": item.get("qty", 0),
                "weight": item.get("weight", 0),
                "avg_cost": item.get("price", 0),
                "market_value": item.get("price", 0) * item.get("qty", 0),
                "source": payload.get("source", "joinquant"),
                "as_of": as_of,
            }
            for item in payload.get("positions", [])
        ]
        orders = [
            {
                "code": order["code"],
                "side": order.get("side", "BUY"),
                "qty": order.get("qty", 0),
                "price": order.get("price", 0),
                "reason": order.get("reason", ""),
                "source": payload.get("source", "joinquant"),
                "ts": as_of,
                "meta": {"note": payload.get("note")},
            }
            for order in payload.get("orders", [])
        ]
        if positions:
            await positions_repo.save_positions(session, positions)
        if orders:
            await signals_repo.insert_signals(session, orders)
        return {"positions": len(positions), "signals": len(orders)}


__all__ = ["JQBridgeService"]
