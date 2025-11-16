import inspect
from datetime import datetime
from typing import Any, Dict, List

from pymongo import ASCENDING

from .base import BaseRepository


class StockBasicRepository(BaseRepository):
    """Persist normalized stock basic records."""

    collection_name = "stock_basic"

    async def ensure_indexes(self) -> None:
        create_index = getattr(self.collection, "create_index", None)
        if not callable(create_index):
            return

        tasks = [
            create_index([("symbol", ASCENDING)], unique=True, name="symbol_unique"),
            create_index([("exchange", ASCENDING)], name="exchange_idx"),
            create_index([("industry", ASCENDING)], name="industry_idx"),
        ]

        for task in tasks:
            if inspect.isawaitable(task):
                await task

    async def upsert_many(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        if not documents:
            return {"matched": 0, "modified": 0, "upserted": 0}

        matched = modified = upserted = 0
        now = datetime.utcnow()

        for payload in documents:
            document = {**payload, "updated_at": now}
            document.setdefault("ingested_at", now)
            filter_query = {"symbol": document["symbol"]}
            update_doc = {
                "$set": document,
                "$setOnInsert": {"created_at": now},
            }
            result = await self.collection.update_one(
                filter_query, update_doc, upsert=True
            )
            matched += getattr(result, "matched_count", 0)
            modified += getattr(result, "modified_count", 0)
            if getattr(result, "upserted_id", None):
                upserted += 1

        return {"matched": matched, "modified": modified, "upserted": upserted}
