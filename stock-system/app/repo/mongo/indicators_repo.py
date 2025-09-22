from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .base import get_database


def get_collection():
    db = get_database()
    return db["indicators"]


async def upsert_indicator_series(
    code: str,
    indicator_name: str,
    params: Dict[str, Any],
    series: Iterable[Dict[str, Any]],
) -> int:
    collection = get_collection()
    count = 0
    for item in series:
        doc = {
            "code": code,
            "indicator_name": indicator_name,
            "date": item["date"].isoformat() if hasattr(item["date"], "isoformat") else item["date"],
            "value": item["value"],
            "params": params,
        }
        filter_doc = {"code": code, "indicator_name": indicator_name, "date": doc["date"]}
        await collection.replace_one(filter_doc, doc, upsert=True)
        count += 1
    return count


async def query_indicator_series(
    code: str,
    indicator_name: str,
    start: str | None,
    end: str | None,
    limit: int,
) -> List[Dict[str, Any]]:
    collection = get_collection()
    cursor = await collection.find({"code": code, "indicator_name": indicator_name})
    results: List[Dict[str, Any]] = []
    async for doc in cursor:
        if start and doc["date"] < start:
            continue
        if end and doc["date"] > end:
            continue
        results.append(doc)
    results.sort(key=lambda item: item["date"])
    return results[:limit] if limit else results


__all__ = ["upsert_indicator_series", "query_indicator_series"]
