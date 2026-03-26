import inspect
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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

    async def find_symbol_records(
        self,
        *,
        symbol: str,
        frequency: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500,
        descending: bool = False,
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {
            "symbol": symbol,
            "frequency": frequency,
        }
        timestamp_filter: Dict[str, datetime] = {}
        if start:
            timestamp_filter["$gte"] = start
        if end:
            timestamp_filter["$lte"] = end
        if timestamp_filter:
            filters["timestamp"] = timestamp_filter

        sort_order = DESCENDING if descending else ASCENDING
        cursor = self.collection.find(filters).sort("timestamp", sort_order)
        if limit > 0:
            cursor = cursor.limit(limit)
        fetch_size = limit if limit > 0 else 1000
        return await cursor.to_list(length=fetch_size)

    async def latest_timestamp(
        self,
        *,
        symbol: str,
        frequency: str,
    ) -> Optional[datetime]:
        document = await self.collection.find_one(
            {"symbol": symbol, "frequency": frequency},
            sort=[("timestamp", DESCENDING)],
            projection={"timestamp": 1},
        )
        if not document:
            return None
        return document.get("timestamp")

    async def list_symbols(
        self,
        *,
        frequency: Optional[str] = None,
        limit: int = 200,
    ) -> List[str]:
        filters: Dict[str, Any] = {}
        if frequency:
            filters["frequency"] = frequency
        items = await self.collection.distinct("symbol", filters)
        symbols = sorted([item for item in items if item])
        if limit > 0:
            return symbols[:limit]
        return symbols
