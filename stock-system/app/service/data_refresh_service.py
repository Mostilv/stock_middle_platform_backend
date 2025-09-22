from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Iterable, List

from ..datasource.akshare_adapter import AkshareAdapter
from ..datasource.baostock_adapter import BaostockAdapter
from ..datasource.base import DummyDataSource
from ..repo.mongo import kline_repo


class DataRefreshService:
    def __init__(self) -> None:
        self.baostock = BaostockAdapter()
        self.akshare = AkshareAdapter()
        self.fallback = DummyDataSource()

    async def refresh_daily(self, codes: Iterable[str], days: int = 5) -> Dict[str, Any]:
        end = date.today()
        start = end - timedelta(days=days)
        summary: Dict[str, Any] = {"inserted": 0}
        for code in codes:
            bars = await self.baostock.get_kline(code, "daily", start, end, "qfq")
            inserted = await kline_repo.upsert_bars(code, "daily", "qfq", bars)
            summary[code] = inserted
            summary["inserted"] += inserted
        return summary

    async def search_stocks(self, query: str | None = None) -> List[Dict[str, Any]]:
        return await self.akshare.list_stocks(query)

    async def get_profile(self, code: str) -> Dict[str, Any]:
        return await self.akshare.get_stock_profile(code)

    async def get_kline(
        self,
        code: str,
        period: str,
        start: date | None,
        end: date | None,
        adjust: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        start_date = start or (date.today() - timedelta(days=30))
        end_date = end or date.today()
        return await kline_repo.query_bars(code, period, start_date, end_date, adjust, limit)

    async def get_fundamentals(self, code: str) -> Dict[str, Any]:
        return await self.fallback.get_fundamentals(code)


__all__ = ["DataRefreshService"]
