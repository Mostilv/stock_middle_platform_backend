import inspect
from datetime import datetime
from typing import Any, Dict, List, Tuple

from pymongo import ASCENDING, DESCENDING

from .base import BaseRepository


class IndicatorDataRepository(BaseRepository):
    """指标数据读写仓储"""

    collection_name = "indicator_data"

    async def ensure_indexes(self) -> None:
        create_index = getattr(self.collection, "create_index", None)
        if not callable(create_index):
            return

        tasks = [
            create_index(
                [
                    ("indicator", ASCENDING),
                    ("symbol", ASCENDING),
                    ("timeframe", ASCENDING),
                    ("timestamp", ASCENDING),
                ],
                name="indicator_symbol_timeframe_timestamp",
                unique=True,
            ),
            create_index(
                [("indicator", ASCENDING), ("timestamp", DESCENDING)],
                name="indicator_timestamp_idx",
                background=True,
            ),
            create_index(
                [("symbol", ASCENDING), ("timestamp", DESCENDING)],
                name="symbol_timestamp_idx",
                background=True,
            ),
        ]

        for task in tasks:
            if inspect.isawaitable(task):
                await task

    async def upsert_many(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        if not documents:
            return {"matched": 0, "modified": 0, "upserted": 0}

        matched = 0
        modified = 0
        upserted = 0
        now = datetime.utcnow()

        for payload in documents:
            document = {**payload, "updated_at": now, "ingested_at": now}
            filter_query = {
                "indicator": document["indicator"],
                "symbol": document["symbol"],
                "timeframe": document["timeframe"],
                "timestamp": document["timestamp"],
            }
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
        self, filters: Dict[str, Any], skip: int, limit: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        cursor = self.collection.find(filters).sort("timestamp", DESCENDING)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        fetch_size = limit if limit and limit > 0 else 100
        results = await cursor.to_list(length=fetch_size)

        count_documents = getattr(self.collection, "count_documents", None)
        if callable(count_documents):
            total = await count_documents(filters)
        else:
            total = len(results)

        return results, total
