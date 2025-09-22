from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def encode_cursor(payload: Dict[str, Any] | None) -> Optional[str]:
    if not payload:
        return None
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str | None) -> Dict[str, Any]:
    if not cursor:
        return {}
    raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    return json.loads(raw)


@dataclass
class Page:
    items: List[Dict[str, Any]]
    next_cursor: Optional[str]


def slice_window(items: Iterable[Dict[str, Any]], limit: int, key: str) -> Page:
    data = list(items)
    if len(data) > limit:
        next_payload = {key: data[limit - 1][key]}
        next_cursor = encode_cursor(next_payload)
        data = data[:limit]
    else:
        next_cursor = None
    return Page(items=data, next_cursor=next_cursor)


__all__ = ["encode_cursor", "decode_cursor", "Page", "slice_window"]
