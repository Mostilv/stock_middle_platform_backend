from datetime import datetime
import inspect
from typing import Any, Dict, List

from pymongo import ASCENDING

from .base import BaseRepository


class QlibStockDataRepository(BaseRepository):
    collection_name = "qlib_stock_data"

    async def ensure_indexes(self) -> None:
        create_index = getattr(self.collection, "create_index", None)
        if callable(create_index):
            tasks = [
                create_index(
                    [
                        ("instrument", ASCENDING),
                        ("freq", ASCENDING),
                        ("datetime", ASCENDING),
                    ],
                    name="instrument_freq_datetime_unique",
                    unique=True,
                ),
                create_index(
                    [("datetime", ASCENDING)],
                    name="qlib_datetime_idx",
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
            document = {**payload}
            document["updated_at"] = now

            filter_query = {
                "instrument": document["instrument"],
                "freq": document["freq"],
                "datetime": document["datetime"],
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
