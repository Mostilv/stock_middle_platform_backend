import inspect
from datetime import datetime
from typing import Any, Dict, List

from pymongo import ASCENDING, DESCENDING

from .base import BaseRepository


class StockKlineRepository(BaseRepository):
    """Persist normalized stock K-line records (all frequencies)."""

    collection_name = "stock_kline"

    async def ensure_indexes(self) -> None:
        create_index = getattr(self.collection, "create_index", None)
        if not callable(create_index):
            return

        tasks = [
            create_index(
                [
                    ("symbol", ASCENDING),
                    ("frequency", ASCENDING),
                    ("timestamp", ASCENDING),
                ],
                unique=True,
                name="symbol_freq_timestamp_unique",
            ),
            create_index(
                [("symbol", ASCENDING), ("timestamp", DESCENDING)],
                name="symbol_timestamp_idx",
                background=True,
            ),
            create_index(
                [("frequency", ASCENDING), ("timestamp", DESCENDING)],
                name="frequency_timestamp_idx",
                background=True,
            ),
        ]

        for task in tasks:
            if inspect.isawaitable(task):
                await task

    async def upsert_many(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        if not documents:
            return {"matched": 0, "modified": 0, "upserted": 0}

        matched = modified = upserted = 0

        for payload in documents:
            timestamp = payload["timestamp"]
            filter_query = {
                "symbol": payload["symbol"],
                "frequency": payload["frequency"],
                "timestamp": timestamp,
            }
            document = {**payload, "updated_at": datetime.utcnow()}
            update_doc = {
                "$set": document,
                "$setOnInsert": {"created_at": datetime.utcnow()},
            }
            result = await self.collection.update_one(
                filter_query, update_doc, upsert=True
            )
            matched += getattr(result, "matched_count", 0)
            modified += getattr(result, "modified_count", 0)
            if getattr(result, "upserted_id", None):
                upserted += 1

        return {"matched": matched, "modified": modified, "upserted": upserted}
