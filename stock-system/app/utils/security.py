from __future__ import annotations

import base64
import hashlib
import hmac
import time

ALLOWED_DRIFT_SECONDS = 120


def sign(payload: bytes | str, timestamp: int | None, secret: str) -> str:
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload
    ts = str(timestamp or int(time.time()))
    message = ts.encode("utf-8") + b"." + payload_bytes
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify(signature: str, payload: bytes | str, timestamp: str, secret: str) -> bool:
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time()) - ts_int) > ALLOWED_DRIFT_SECONDS:
        return False
    expected = sign(payload, ts_int, secret)
    return hmac.compare_digest(signature, expected)


__all__ = ["sign", "verify", "ALLOWED_DRIFT_SECONDS"]
