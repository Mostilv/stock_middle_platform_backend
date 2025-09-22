from __future__ import annotations

from typing import Dict

from .data_refresh_service import DataRefreshService


class FundamentalsService:
    def __init__(self, data_service: DataRefreshService) -> None:
        self.data_service = data_service

    async def get_snapshot(self, code: str, period: str) -> Dict[str, object]:
        fundamentals = await self.data_service.get_fundamentals(code)
        fundamentals["period"] = period
        return fundamentals

    async def get_timeline(self, code: str, limit: int = 8) -> Dict[str, object]:
        snapshot = await self.data_service.get_fundamentals(code)
        items = [snapshot]
        return {"items": items[:limit]}


__all__ = ["FundamentalsService"]
