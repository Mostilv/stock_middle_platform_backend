import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import akshare as ak
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import UpdateOne

from app.db.database import db_manager

logger = logging.getLogger(__name__)


class BaseIndicatorCalculator(ABC):
    """自定义指标计算器抽象基类"""

    key: str
    name: str
    description: str
    target: str
    source: str = "unknown"
    default_params: Dict[str, Any] = {}
    allow_target_override: bool = False

    async def run(
        self,
        target: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """执行指标计算并返回结果数据集"""

        actual_target = target if (target and self.allow_target_override) else self.target
        params = {**self.default_params, **(params or {})}

        df = await self.fetch_source_data(actual_target, start, end, params)
        if df.empty:
            return pd.DataFrame()

        result = self.compute_indicator(df, params)
        if result.empty:
            return result

        if "timestamp" not in result.columns:
            raise ValueError("指标结果缺少timestamp列")

        result = result.copy()
        result["target"] = actual_target
        result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce")
        result = result.dropna(subset=["timestamp"])
        result = result.sort_values("timestamp")
        result = result.drop_duplicates(subset=["timestamp", "target"], keep="last")
        return result

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "target": self.target,
            "source": self.source,
            "default_params": self.default_params,
            "allow_target_override": self.allow_target_override,
        }

    @abstractmethod
    async def fetch_source_data(
        self,
        target: str,
        start: Optional[datetime],
        end: Optional[datetime],
        params: Dict[str, Any],
    ) -> pd.DataFrame:
        """获取指标计算所需的原始数据"""

    @abstractmethod
    def compute_indicator(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """根据原始数据计算指标"""


class ShanghaiCompositeMACDCalculator(BaseIndicatorCalculator):
    key = "macd_shanghai_composite"
    name = "上证指数MACD"
    description = "基于上证指数日线收盘价的MACD指标"
    target = "sh000001"
    source = "akshare"
    default_params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
    allow_target_override = False

    async def fetch_source_data(
        self,
        target: str,
        start: Optional[datetime],
        end: Optional[datetime],
        params: Dict[str, Any],
    ) -> pd.DataFrame:
        loop = asyncio.get_running_loop()

        def _fetch() -> pd.DataFrame:
            data = ak.stock_zh_index_daily(symbol=target)
            if data is None or data.empty:
                return pd.DataFrame()

            data = data.copy()
            if "date" not in data.columns:
                return pd.DataFrame()

            data["date"] = pd.to_datetime(data["date"], errors="coerce")
            data = data.dropna(subset=["date"])
            data = data.sort_values("date")

            if start:
                data = data[data["date"] >= start]
            if end:
                data = data[data["date"] <= end]

            return data

        return await loop.run_in_executor(None, _fetch)

    def compute_indicator(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        if "close" not in df.columns:
            raise ValueError("原始数据缺少close列，无法计算MACD")

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])

        fast = int(params.get("fast_period", 12))
        slow = int(params.get("slow_period", 26))
        signal = int(params.get("signal_period", 9))

        if fast <= 0 or slow <= 0 or signal <= 0:
            raise ValueError("MACD参数必须为正整数")

        close_series = df["close"]
        ema_fast = close_series.ewm(span=fast, adjust=False).mean()
        ema_slow = close_series.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd = (dif - dea) * 2

        result = pd.DataFrame(
            {
                "timestamp": df["date"],
                "dif": dif,
                "dea": dea,
                "macd": macd,
            }
        )

        result = result.dropna(subset=["dif", "dea", "macd"])
        return result


class IndicatorCalculationService:
    """管理自定义指标计算与存储的服务"""

    def __init__(self) -> None:
        self._collection_name = "custom_indicator_values"
        self._calculators: Dict[str, BaseIndicatorCalculator] = {
            calc.key: calc for calc in [ShanghaiCompositeMACDCalculator()]
        }

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return db_manager.get_mongodb_collection(self._collection_name)

    def list_indicators(self) -> List[Dict[str, Any]]:
        return [calculator.metadata for calculator in self._calculators.values()]

    def _resolve_calculator(self, key: str) -> BaseIndicatorCalculator:
        calculator = self._calculators.get(key)
        if not calculator:
            raise KeyError(f"未找到指标计算器: {key}")
        return calculator

    @staticmethod
    def _normalize_dates(
        start: Optional[date], end: Optional[date]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        start_dt = datetime.combine(start, datetime.min.time()) if start else None
        end_dt = datetime.combine(end, datetime.max.time()) if end else None
        if start_dt and end_dt and start_dt > end_dt:
            raise ValueError("开始日期不能晚于结束日期")
        return start_dt, end_dt

    async def compute_and_store(
        self,
        indicator_key: str,
        *,
        start: Optional[date] = None,
        end: Optional[date] = None,
        target: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, str]:
        calculator = self._resolve_calculator(indicator_key)
        start_dt, end_dt = self._normalize_dates(start, end)

        result_df = await calculator.run(target=target, start=start_dt, end=end_dt, params=params)
        if result_df.empty:
            logger.info("指标 %s 在给定区间内无计算结果", indicator_key)
            return 0, target or calculator.target

        operations: List[UpdateOne] = []
        now = datetime.utcnow()
        merged_params = {**calculator.default_params, **(params or {})}
        effective_target = result_df["target"].iloc[0] if "target" in result_df.columns else (target or calculator.target)

        for record in result_df.to_dict("records"):
            timestamp = pd.to_datetime(record.get("timestamp"), errors="coerce")
            if pd.isna(timestamp):
                continue

            timestamp_dt = timestamp.to_pydatetime()
            target_value = record.get("target", calculator.target)
            values = {
                key: value
                for key, value in record.items()
                if key not in {"timestamp", "target"}
            }

            for key, value in list(values.items()):
                if isinstance(value, float) and pd.isna(value):
                    values[key] = None

            operations.append(
                UpdateOne(
                    {
                        "indicator": indicator_key,
                        "target": target_value,
                        "timestamp": timestamp_dt,
                    },
                    {
                        "$set": {
                            "indicator": indicator_key,
                            "target": target_value,
                            "timestamp": timestamp_dt,
                            "values": values,
                            "params": merged_params,
                            "source": calculator.source,
                        },
                        "$setOnInsert": {"created_at": now},
                        "$currentDate": {"updated_at": True},
                    },
                    upsert=True,
                )
            )

        if not operations:
            return 0, effective_target

        result = await self.collection.bulk_write(operations, ordered=False)
        modified = (result.upserted_count or 0) + (result.modified_count or 0)
        logger.info("指标 %s 数据写入完成，共更新 %s 条", indicator_key, modified)
        return modified, effective_target

    async def fetch_indicator_series(
        self,
        indicator_key: str,
        *,
        start: Optional[date] = None,
        end: Optional[date] = None,
        target: Optional[str] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        calculator = self._resolve_calculator(indicator_key)
        start_dt, end_dt = self._normalize_dates(start, end)

        query: Dict[str, Any] = {"indicator": indicator_key}
        target_value = target or calculator.target
        query["target"] = target_value

        if start_dt or end_dt:
            query["timestamp"] = {}
            if start_dt:
                query["timestamp"]["$gte"] = start_dt
            if end_dt:
                query["timestamp"]["$lte"] = end_dt

        cursor = self.collection.find(query).sort("timestamp", 1)
        if limit:
            cursor = cursor.limit(limit)

        records = await cursor.to_list(length=limit)
        for record in records:
            record["id"] = str(record.pop("_id"))
            timestamp_value = record.get("timestamp")
            if isinstance(timestamp_value, datetime):
                record["timestamp"] = timestamp_value.isoformat()

        return {
            "indicator": indicator_key,
            "target": target_value,
            "metadata": calculator.metadata,
            "records": records,
        }
