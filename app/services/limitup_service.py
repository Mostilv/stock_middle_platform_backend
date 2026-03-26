import datetime
from typing import Dict, Optional

from app.db import db_manager
from app.models.limitup import LimitUpOverview
from app.services.collection_service import BaseCollectionService


def _today_iso() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


class LimitUpService(BaseCollectionService):
    DEFAULT_OVERVIEW = {
        "date": "2025-08-28",
        "sectors": [
            {"name": "芯片", "count": 27, "value": 21441},
            {"name": "算力", "count": 29, "value": 8221},
            {"name": "人工智能", "count": 31, "value": 7592},
            {"name": "通信", "count": 9, "value": 4830},
            {"name": "证券", "count": 2, "value": 4187},
        ],
        "ladders": [],
    }

    def __init__(self) -> None:
        super().__init__("limitup_overview")

    async def get_overview(self, date: Optional[str]) -> LimitUpOverview:
        target_date = date or _today_iso()
        pool_col = db_manager.get_mongodb_collection("limit_up_pool")
        if not date:
            latest_doc = await pool_col.find_one({}, sort=[("date", -1)])
            if latest_doc:
                target_date = latest_doc["date"]

        stocks = await pool_col.find({"date": target_date}).to_list(length=None)
        if not stocks:
            await self._ensure_seeded()
            document = await self.collection.find_one({}) or self.DEFAULT_OVERVIEW
            return LimitUpOverview.parse_obj(self.strip_id(document))

        ladders_map: Dict[int, list] = {}
        sectors_map: Dict[str, Dict[str, float]] = {}
        for item in stocks:
            days = int(item.get("limitUpDays", 1) or 1)
            ladders_map.setdefault(days, []).append(
                {
                    "name": item.get("name", ""),
                    "code": item.get("code", ""),
                    "time": item.get("firstLimitUpTime", "")[:5]
                    if item.get("firstLimitUpTime")
                    else "",
                    "price": item.get("price", 0),
                    "changePercent": item.get("changePercent", 0),
                    "volume1": round(item.get("limitUpFund", 0) / 10000, 2)
                    if item.get("limitUpFund")
                    else 0,
                    "volume2": 0,
                    "ratio1": 0,
                    "ratio2": 0,
                    "sectors": [item.get("industry")] if item.get("industry") else [],
                    "marketCap": round(item.get("marketCap", 0) / 100000000, 2)
                    if item.get("marketCap")
                    else 0,
                    "pe": 0,
                    "pb": 0,
                }
            )
            industry = item.get("industry", "未知")
            if industry:
                sectors_map.setdefault(industry, {"count": 0, "value": 0})
                sectors_map[industry]["count"] += 1
                sectors_map[industry]["value"] += item.get("amount", 0) / 10000

        ladders = [
            {
                "level": level,
                "count": len(ladders_map[level]),
                "stocks": ladders_map[level],
            }
            for level in sorted(ladders_map.keys(), reverse=True)
        ]
        sectors = sorted(
            [
                {
                    "name": name,
                    "count": int(data["count"]),
                    "value": int(data["value"]),
                }
                for name, data in sectors_map.items()
            ],
            key=lambda item: item["count"],
            reverse=True,
        )[:10]

        return LimitUpOverview.parse_obj(
            {
                "date": target_date,
                "sectors": sectors,
                "ladders": ladders,
            }
        )

    async def _ensure_seeded(self) -> None:
        if await self.collection.count_documents({}) > 0:
            return
        await self.collection.insert_one(
            {**self.DEFAULT_OVERVIEW, "updated_at": datetime.datetime.utcnow()}
        )
