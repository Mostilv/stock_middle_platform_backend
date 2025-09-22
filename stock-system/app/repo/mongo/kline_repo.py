from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List

from .base import get_database


COLLECTION_MAP = {
    "daily": "kline_daily",
    "weekly": "kline_weekly",
    "monthly": "kline_monthly",
}


def get_collection(period: str):
    db = get_database()
    name = COLLECTION_MAP.get(period, "kline_daily")
    return db[name]


async def upsert_bars(
    code: str,
    period: str,
    adjust: str,
    bars: Iterable[Dict[str, Any]],
) -> int:
    collection = get_collection(period)
    count = 0
    for bar in bars:
        doc: Dict[str, Any] = dict(bar)
        doc.update({"code": code, "period": period, "adjust": adjust})
        filter_doc = {"code": code, "date": doc["date"], "adjust": adjust}
        await collection.replace_one(filter_doc, doc, upsert=True)
        count += 1
    return count


async def query_bars(
    code: str,
    period: str,
    start: date | None,
    end: date | None,
    adjust: str,
    limit: int,
) -> List[Dict[str, Any]]:
    collection = get_collection(period)
    cursor = await collection.find({"code": code, "adjust": adjust})
    results: List[Dict[str, Any]] = []
    async for doc in cursor:
        if start and doc["date"] < start.isoformat():
            continue
        if end and doc["date"] > end.isoformat():
            continue
        results.append(doc)
    results.sort(key=lambda item: item["date"])
    return results[:limit] if limit else results


__all__ = ["upsert_bars", "query_bars"]
