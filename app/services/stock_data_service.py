import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import baostock as bs
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import UpdateOne

from app.config import settings
from app.db.database import db_manager

logger = logging.getLogger(__name__)


class StockDataService:
    """负责从baostock拉取股票数据并写入MongoDB"""

    def __init__(self) -> None:
        self._login_lock = asyncio.Lock()
        self._daily_collection_name = "stock_daily_bars"
        self._minute_collection_name = "stock_minute_bars"
        self._fundamental_collection_name = "stock_fundamentals"

    @property
    def daily_collection(self) -> AsyncIOMotorCollection:
        return db_manager.get_mongodb_collection(self._daily_collection_name)

    @property
    def minute_collection(self) -> AsyncIOMotorCollection:
        return db_manager.get_mongodb_collection(self._minute_collection_name)

    @property
    def fundamental_collection(self) -> AsyncIOMotorCollection:
        return db_manager.get_mongodb_collection(self._fundamental_collection_name)

    async def ingest_minute_bars(self, code: str, start: date, end: date) -> int:
        """获取1分钟级别的K线数据并保存到MongoDB"""

        if start > end:
            raise ValueError("开始日期不能晚于结束日期")

        df = await self._query_minute_bars(code, start, end)
        if df.empty:
            logger.info("⏱️ %s 在 %s 到 %s 范围内无分钟级数据", code, start, end)
            return 0

        records = self._clean_minute_bars(df, code)
        if not records:
            return 0

        operations = [
            UpdateOne(
                {
                    "code": record["code"],
                    "timestamp": record["timestamp"],
                    "frequency": record["frequency"],
                },
                {
                    "$set": {k: v for k, v in record.items() if k not in {"created_at"}},
                    "$setOnInsert": {"created_at": record["created_at"]},
                    "$currentDate": {"updated_at": True},
                },
                upsert=True,
            )
            for record in records
        ]

        if not operations:
            return 0

        result = await self.minute_collection.bulk_write(operations, ordered=False)
        modified = (result.upserted_count or 0) + (result.modified_count or 0)
        logger.info("📈 %s 分钟级数据写入完成，新增/更新 %s 条", code, modified)
        return modified

    async def ingest_fundamental_data(self, code: str, start: date, end: date) -> int:
        """获取基本面数据并保存到MongoDB"""

        if start > end:
            raise ValueError("开始日期不能晚于结束日期")

        quarters = self._iter_quarters(start, end)
        total_modified = 0

        for year, quarter in quarters:
            df = await self._query_profit_data(code, year, quarter)
            if df.empty:
                continue

            records = self._clean_fundamental_data(df, code, year, quarter)
            if not records:
                continue

            operations = [
                UpdateOne(
                    {
                        "code": record["code"],
                        "report_date": record["report_date"],
                        "year": record["year"],
                        "quarter": record["quarter"],
                    },
                    {
                        "$set": {k: v for k, v in record.items() if k not in {"created_at"}},
                        "$setOnInsert": {"created_at": record["created_at"]},
                        "$currentDate": {"updated_at": True},
                    },
                    upsert=True,
                )
                for record in records
            ]

            if not operations:
                continue

            result = await self.fundamental_collection.bulk_write(operations, ordered=False)
            modified = (result.upserted_count or 0) + (result.modified_count or 0)
            total_modified += modified

        logger.info("🧾 %s 基本面数据写入完成，总计 %s 条", code, total_modified)
        return total_modified

    async def reconcile_recent_daily_bars(
        self,
        code: str,
        lookback_trading_days: int = 7,
        *,
        threshold: Optional[float] = None,
        full_history_start: Optional[date] = None,
    ) -> Dict[str, Any]:
        """校验近N个交易日的日线数据，按需触发全量或增量更新。

        Args:
            code: 股票代码，例如"sh.600000"。
            lookback_trading_days: 需要对账的交易日数量。
            threshold: 允许的关键字段绝对百分比误差，默认读取配置。
            full_history_start: 全量刷新时的起始日期，默认1990-01-01。

        Returns:
            包含处理状态与统计信息的字典。
        """

        if lookback_trading_days <= 0:
            raise ValueError("lookback_trading_days 必须为正数")

        threshold_to_use = (
            threshold if threshold is not None else settings.stock_daily_anomaly_threshold
        )
        if threshold_to_use < 0:
            raise ValueError("threshold 不能为负数")

        buffer_days = max(lookback_trading_days * 3, 21)
        today = date.today()
        start = today - timedelta(days=buffer_days)

        daily_df = await self._query_daily_bars(code, start, today)
        if daily_df.empty:
            logger.warning("📭 %s 在最近窗口内未返回任何日线数据", code)
            return {
                "code": code,
                "status": "no_data",
                "lookback_trading_days": lookback_trading_days,
                "modified": 0,
                "anomalies": [],
                "missing_dates": [],
            }

        cleaned_records = self._clean_daily_bars(daily_df, code)
        if not cleaned_records:
            logger.warning("🧹 %s 日线数据清洗后为空", code)
            return {
                "code": code,
                "status": "no_data",
                "lookback_trading_days": lookback_trading_days,
                "modified": 0,
                "anomalies": [],
                "missing_dates": [],
            }

        recent_records = cleaned_records[-lookback_trading_days:]
        if not recent_records:
            logger.warning("📭 %s 未获取到足够的交易日用于对账", code)
            return {
                "code": code,
                "status": "no_data",
                "lookback_trading_days": lookback_trading_days,
                "modified": 0,
                "anomalies": [],
                "missing_dates": [],
            }

        lookback_start = recent_records[0]["trade_date"]
        existing_cursor = self.daily_collection.find(
            {"code": code, "trade_date": {"$gte": lookback_start}}
        ).sort("trade_date", 1)
        existing_docs = await existing_cursor.to_list(length=None)
        existing_map: Dict[date, Dict[str, Any]] = {}
        for doc in existing_docs:
            trade_dt: datetime = doc.get("trade_date")  # type: ignore[assignment]
            if isinstance(trade_dt, datetime):
                existing_map[trade_dt.date()] = doc

        key_fields = ["close_adj", "open", "high", "low"]
        anomalies: List[Dict[str, Any]] = []
        missing_dates: List[str] = []

        for record in recent_records:
            trade_dt: datetime = record["trade_date"]
            existing = existing_map.get(trade_dt.date())
            if not existing:
                missing_dates.append(trade_dt.date().isoformat())
                continue

            for field in key_fields:
                new_value = record.get(field)
                old_value = existing.get(field)

                if new_value is None and old_value is None:
                    continue
                if (new_value is None) != (old_value is None):
                    anomalies.append(
                        {
                            "date": trade_dt.date().isoformat(),
                            "field": field,
                            "old": old_value,
                            "new": new_value,
                            "error": None,
                        }
                    )
                    break

                assert new_value is not None and old_value is not None  # for type checker
                denominator = abs(old_value) if abs(old_value) > 1e-9 else None
                if denominator is None:
                    if abs(new_value - old_value) > threshold_to_use:
                        anomalies.append(
                            {
                                "date": trade_dt.date().isoformat(),
                                "field": field,
                                "old": old_value,
                                "new": new_value,
                                "error": None,
                            }
                        )
                        break
                    continue

                pct_error = abs(new_value - old_value) / denominator
                if pct_error > threshold_to_use:
                    anomalies.append(
                        {
                            "date": trade_dt.date().isoformat(),
                            "field": field,
                            "old": old_value,
                            "new": new_value,
                            "error": pct_error,
                        }
                    )
                    break

        if anomalies or missing_dates:
            logger.warning(
                "🛟 %s 日线数据检测到异常或缺失，触发全量刷新。缺失:%s, 异常:%s",
                code,
                missing_dates,
                anomalies,
            )
            history_start = full_history_start or date(1990, 1, 1)
            if history_start > today:
                raise ValueError("full_history_start 不能晚于今日")
            refreshed = await self._full_refresh_daily_history(
                code,
                start_date=history_start,
                end_date=today,
            )
            return {
                "code": code,
                "status": "full_refresh",
                "lookback_trading_days": lookback_trading_days,
                "modified": refreshed,
                "anomalies": anomalies,
                "missing_dates": missing_dates,
            }

        modified = await self._upsert_daily_records(recent_records)
        logger.info(
            "✅ %s 日线数据近 %s 个交易日校验通过，已完成增量更新 %s 条",
            code,
            lookback_trading_days,
            modified,
        )
        return {
            "code": code,
            "status": "incremental",
            "lookback_trading_days": lookback_trading_days,
            "modified": modified,
            "anomalies": [],
            "missing_dates": [],
        }

    async def reconcile_daily_bars_for_codes(
        self,
        codes: List[str],
        lookback_trading_days: int = 7,
        *,
        threshold: Optional[float] = None,
        full_history_start: Optional[date] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """批量执行日线数据的日终校验任务。"""

        results: Dict[str, Dict[str, Any]] = {}
        for code in codes:
            try:
                results[code] = await self.reconcile_recent_daily_bars(
                    code,
                    lookback_trading_days,
                    threshold=threshold,
                    full_history_start=full_history_start,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("❌ %s 日线对账任务执行失败", code)
                results[code] = {
                    "code": code,
                    "status": "error",
                    "detail": str(exc),
                }
        return results

    async def _query_minute_bars(self, code: str, start: date, end: date) -> pd.DataFrame:
        fields = (
            "time,code,open,high,low,close,volume,amount,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM"
        )

        def _fetch() -> pd.DataFrame:
            rs = bs.query_history_k_data_plus(
                code,
                fields,
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
                frequency="1",
                adjustflag="3",
            )
            if rs.error_code != "0":
                raise RuntimeError(f"获取分钟数据失败: {rs.error_msg}")
            data: List[List[str]] = []
            while (rs.error_code == "0") and rs.next():
                data.append(rs.get_row_data())
            return pd.DataFrame(data, columns=rs.fields)

        return await self._execute_with_login(_fetch)

    async def _query_daily_bars(self, code: str, start: date, end: date) -> pd.DataFrame:
        fields = (
            "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg"
        )

        def _fetch() -> pd.DataFrame:
            rs = bs.query_history_k_data_plus(
                code,
                fields,
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
                frequency="d",
                adjustflag="3",
            )
            if rs.error_code != "0":
                raise RuntimeError(f"获取日线数据失败: {rs.error_msg}")
            data: List[List[str]] = []
            while (rs.error_code == "0") and rs.next():
                data.append(rs.get_row_data())
            return pd.DataFrame(data, columns=rs.fields)

        return await self._execute_with_login(_fetch)

    async def _query_profit_data(self, code: str, year: int, quarter: int) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
            if rs.error_code != "0":
                logger.warning("获取利润表失败: %s", rs.error_msg)
                return pd.DataFrame()
            data: List[List[str]] = []
            while (rs.error_code == "0") and rs.next():
                data.append(rs.get_row_data())
            return pd.DataFrame(data, columns=rs.fields)

        return await self._execute_with_login(_fetch)

    async def _execute_with_login(self, func) -> pd.DataFrame:
        async with self._login_lock:
            loop = asyncio.get_running_loop()

            def _wrapped() -> pd.DataFrame:
                lg = bs.login(settings.baostock_user, settings.baostock_password)
                if lg.error_code != "0":
                    raise RuntimeError(f"baostock登录失败: {lg.error_msg}")
                try:
                    return func()
                finally:
                    bs.logout()

            return await loop.run_in_executor(None, _wrapped)

    def _clean_minute_bars(self, df: pd.DataFrame, code: str) -> List[Dict]:
        if df.empty:
            return []

        df = df.copy()
        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "turn",
            "pctChg",
            "peTTM",
            "pbMRQ",
            "psTTM",
            "pcfNcfTTM",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.dropna(subset=["time", "open", "close"])
        df = df.drop_duplicates(subset=["time", "code"], keep="last")
        df["timestamp"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["code"] = code
        df["frequency"] = "1m"

        records: List[Dict] = []
        now = datetime.utcnow()
        for record in df.to_dict("records"):
            record["timestamp"] = pd.to_datetime(record["timestamp"]).to_pydatetime()
            record["created_at"] = now
            for key, value in list(record.items()):
                if isinstance(value, float) and pd.isna(value):
                    record[key] = None
            records.append(record)

        return records

    def _clean_daily_bars(self, df: pd.DataFrame, code: str) -> List[Dict[str, Any]]:
        if df.empty:
            return []

        df = df.copy()

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "preclose",
            "volume",
            "amount",
            "turn",
            "pctChg",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.dropna(subset=["date", "close"])
        df = df.drop_duplicates(subset=["date", "code"], keep="last")
        df["trade_date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["trade_date"])
        df = df.sort_values("trade_date")
        df["code"] = code
        df["close_adj"] = df["close"]
        df = df.rename(columns={"pctChg": "pct_chg"})

        records: List[Dict[str, Any]] = []
        now = datetime.utcnow()
        for record in df.to_dict("records"):
            record["trade_date"] = pd.to_datetime(record["trade_date"]).to_pydatetime()
            record["created_at"] = now
            record["frequency"] = "1d"
            # 替换 NaN 为 None，便于MongoDB存储
            for key, value in list(record.items()):
                if isinstance(value, float) and pd.isna(value):
                    record[key] = None
            records.append(record)

        return records

    async def _upsert_daily_records(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0

        operations = [
            UpdateOne(
                {"code": record["code"], "trade_date": record["trade_date"]},
                {
                    "$set": {k: v for k, v in record.items() if k not in {"created_at"}},
                    "$setOnInsert": {"created_at": record["created_at"]},
                    "$currentDate": {"updated_at": True},
                },
                upsert=True,
            )
            for record in records
        ]

        result = await self.daily_collection.bulk_write(operations, ordered=False)
        modified = (result.upserted_count or 0) + (result.modified_count or 0)
        return modified

    async def _full_refresh_daily_history(
        self,
        code: str,
        *,
        start_date: date,
        end_date: date,
    ) -> int:
        history_df = await self._query_daily_bars(code, start_date, end_date)
        records = self._clean_daily_bars(history_df, code)
        if not records:
            logger.warning("⚠️ %s 全量刷新时未获取到任何日线数据", code)
            await self.daily_collection.delete_many({"code": code})
            return 0

        await self.daily_collection.delete_many({"code": code})

        now = datetime.utcnow()
        for record in records:
            record["updated_at"] = now

        inserted = 0
        batch_size = 1000
        for idx in range(0, len(records), batch_size):
            batch = records[idx : idx + batch_size]
            if not batch:
                continue
            result = await self.daily_collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)

        logger.info("🧼 %s 全量刷新日线完成，共写入 %s 条", code, inserted)
        return inserted

    def _clean_fundamental_data(
        self, df: pd.DataFrame, code: str, year: int, quarter: int
    ) -> List[Dict]:
        if df.empty:
            return []

        df = df.copy()

        numeric_columns = [
            "roe",
            "npMargin",
            "gpMargin",
            "netProfit",
            "epsTTM",
            "mbRevenue",
            "totalShare",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.dropna(subset=["report_date"])
        df = df.drop_duplicates(subset=["report_date", "code"], keep="last")
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
        df = df.dropna(subset=["report_date"])
        df["code"] = code
        df["year"] = year
        df["quarter"] = quarter

        records: List[Dict] = []
        now = datetime.utcnow()
        for record in df.to_dict("records"):
            record["report_date"] = pd.to_datetime(record["report_date"]).to_pydatetime()
            record["created_at"] = now
            for key, value in list(record.items()):
                if isinstance(value, float) and pd.isna(value):
                    record[key] = None
            records.append(record)

        return records

    @staticmethod
    def _iter_quarters(start: date, end: date) -> List[Tuple[int, int]]:
        quarters: List[Tuple[int, int]] = []
        current = date(start.year, start.month, 1)
        stop = date(end.year, end.month, 1)

        while current <= stop:
            quarter = (current.month - 1) // 3 + 1
            quarters.append((current.year, quarter))
            month = current.month + 3
            year = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            current = date(year, month, 1)

        return quarters
