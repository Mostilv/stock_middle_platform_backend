from __future__ import annotations

import abc
from datetime import date, timedelta
from typing import Any, Dict, List


class BaseDataSource(abc.ABC):
    name: str

    @abc.abstractmethod
    async def list_stocks(self, query: str | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_stock_profile(self, code: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_kline(
        self,
        code: str,
        period: str,
        start: date,
        end: date,
        adjust: str,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_fundamentals(self, code: str) -> Dict[str, Any]:
        raise NotImplementedError


class DummyDataSource(BaseDataSource):
    name = "dummy"

    def __init__(self) -> None:
        self._profiles = {
            "600519": {
                "code": "600519",
                "name": "贵州茅台",
                "market": "SSE",
                "list_date": "2001-08-27",
                "industry": "饮料制造",
                "valuation": {"pe_ttm": 32.1, "pb": 8.7, "ps_ttm": 11.2},
                "shares": {"total": 1_250_000_000, "float": 620_000_000},
                "indices": ["000300", "000905"],
            },
            "000001": {
                "code": "000001",
                "name": "平安银行",
                "market": "SZSE",
                "list_date": "1991-04-03",
                "industry": "银行",
                "valuation": {"pe_ttm": 10.5, "pb": 1.1, "ps_ttm": 3.2},
                "shares": {"total": 19_405_918_198, "float": 15_000_000_000},
                "indices": ["000001", "399001"],
            },
        }

    async def list_stocks(self, query: str | None = None) -> List[Dict[str, Any]]:
        items = list(self._profiles.values())
        if query:
            items = [item for item in items if query in item["name"] or query in item["code"]]
        return items

    async def get_stock_profile(self, code: str) -> Dict[str, Any]:
        return self._profiles.get(code, {"code": code, "name": code})

    async def get_kline(
        self,
        code: str,
        period: str,
        start: date,
        end: date,
        adjust: str,
    ) -> List[Dict[str, Any]]:
        bars: List[Dict[str, Any]] = []
        delta = max((end - start).days, 0)
        for idx in range(delta + 1):
            day = start + timedelta(days=idx)
            if day > end:
                break
            bars.append(
                {
                    "date": day.isoformat(),
                    "open": 1500 + idx,
                    "high": 1510 + idx,
                    "low": 1490 + idx,
                    "close": 1505 + idx,
                    "volume": 1_000_000 + idx * 1000,
                    "turnover": 10_000_000 + idx * 10_000,
                }
            )
        return bars

    async def get_fundamentals(self, code: str) -> Dict[str, Any]:
        return {
            "code": code,
            "period": "ttm",
            "metrics": {
                "revenue": 1500e8,
                "net_profit": 550e8,
                "roe": 28.3,
                "gross_margin": 91.2,
                "debt_to_assets": 24.7,
            },
            "report_date": "2025-06-30",
        }


__all__ = ["BaseDataSource", "DummyDataSource"]
