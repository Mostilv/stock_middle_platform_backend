from typing import Dict, Optional, Tuple

import pandas as pd

from app.utils.data_sources import data_source_manager


class IndicatorService:
    def __init__(self, manager=data_source_manager) -> None:
        self.manager = manager

    async def get_stock_list(self, source: str) -> Dict[str, object]:
        data = (
            self.manager.get_stock_list_bs()
            if source == "baostock"
            else self.manager.get_stock_list_ak()
        )
        if data is None:
            raise ValueError("获取股票列表失败")
        return self._format_collection(data)

    async def get_stock_history(
        self, stock_code: str, start_date: str, end_date: str, source: str
    ) -> Dict[str, object]:
        if source == "baostock":
            data = self.manager.get_stock_data_bs(stock_code, start_date, end_date)
        else:
            data = self.manager.get_stock_data_ak(stock_code, start_date, end_date)

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise LookupError("股票数据不存在")
        return self._format_collection(data)

    async def get_stock_realtime(self, stock_code: str) -> Dict[str, object]:
        data = self.manager.get_stock_realtime_ak(stock_code)
        if data is None:
            raise LookupError("股票实时数据不存在")
        return {"data": data}

    async def get_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, object]:
        data = self.manager.get_index_data_ak(index_code)
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise LookupError("指数数据不存在")

        if start_date and end_date and isinstance(data, pd.DataFrame):
            data = data[(data.index >= start_date) & (data.index <= end_date)]
        return self._format_collection(data)

    async def get_market_overview(self) -> Dict[str, object]:
        indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指",
        }

        market_data: Dict[str, object] = {}
        for code, name in indices.items():
            try:
                dataset = self.manager.get_index_data_ak(code)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"获取指数 {code} 数据失败: {exc}")
                continue

            if dataset is None or dataset.empty:
                continue

            latest = dataset.iloc[-1]
            market_data[code] = {
                "name": name,
                "code": code,
                "latest_price": latest.get("close", 0),
                "change": latest.get("change", 0),
                "change_pct": latest.get("pct_chg", 0),
                "volume": latest.get("volume", 0),
                "amount": latest.get("amount", 0),
            }

        return {"data": market_data}

    @staticmethod
    def _format_collection(data) -> Dict[str, object]:
        records, total = IndicatorService._normalize_data(data)
        return {"data": records, "total": total}

    @staticmethod
    def _normalize_data(data) -> Tuple[object, int]:
        if isinstance(data, pd.DataFrame):
            records = data.to_dict("records")
            return records, len(records)

        if isinstance(data, list):
            return data, len(data)

        if isinstance(data, dict):
            return data, 1

        return data or [], len(data) if hasattr(data, "__len__") else int(bool(data))

