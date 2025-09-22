from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from .base import BaseDataSource, DummyDataSource


class AkshareAdapter(BaseDataSource):
    name = "akshare"

    def __init__(self) -> None:
        self._fallback = DummyDataSource()

    async def list_stocks(self, query: str | None = None) -> List[Dict[str, Any]]:
        return await self._fallback.list_stocks(query)

    async def get_stock_profile(self, code: str) -> Dict[str, Any]:
        return await self._fallback.get_stock_profile(code)

    async def get_kline(
        self,
        code: str,
        period: str,
        start: date,
        end: date,
        adjust: str,
    ) -> List[Dict[str, Any]]:
        return await self._fallback.get_kline(code, period, start, end, adjust)

    async def get_fundamentals(self, code: str) -> Dict[str, Any]:
        return await self._fallback.get_fundamentals(code)


__all__ = ["AkshareAdapter"]
