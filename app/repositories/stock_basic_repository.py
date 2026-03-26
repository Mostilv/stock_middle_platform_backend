import inspect
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING

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

    async def find_records(
        self,
        *,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {}
        if symbol:
            filters["symbol"] = symbol
        if exchange:
            filters["exchange"] = exchange
        if industry:
            filters["industry"] = industry

        cursor = self.collection.find(filters).sort(
            [("symbol", ASCENDING), ("updated_at", DESCENDING)]
        )
        if limit > 0:
            cursor = cursor.limit(limit)
        fetch_size = limit if limit > 0 else 1000
        return await cursor.to_list(length=fetch_size)

    async def list_symbols(self, *, limit: int = 200) -> List[str]:
        items = await self.collection.distinct("symbol")
        symbols = sorted([item for item in items if item])
        if limit > 0:
            return symbols[:limit]
        return symbols
