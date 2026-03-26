from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.core.data_sinks import DataSinkRegistry, data_sink_registry
from app.models.indicator import IndicatorRecord
from app.models.indicator_runtime import (
    IndicatorComputeRequest,
    IndicatorComputeResponse,
    IndicatorComputeResult,
    IndicatorSeriesPoint,
)
from app.repositories.indicator_repository import IndicatorDataRepository
from app.repositories.stock_kline_repository import StockKlineRepository


class DatabaseIndicatorService:
    def __init__(
        self,
        *,
        registry: Optional[DataSinkRegistry] = None,
        indicator_repository: Optional[IndicatorDataRepository] = None,
    ) -> None:
        self.registry = registry or data_sink_registry
        self._kline_repositories: Dict[str, StockKlineRepository] = {}
        self._indicator_repositories: Dict[str, IndicatorDataRepository] = {}
        self._default_indicator_repository = indicator_repository

    async def calculate(self, payload: IndicatorComputeRequest) -> IndicatorComputeResponse:
        repository = self._get_kline_repository(payload.target)
        documents = await repository.find_symbol_records(
            symbol=payload.symbol,
            frequency=payload.frequency,
            limit=payload.lookback,
            descending=False,
        )
        if not documents:
            raise ValueError(f"No K-line data found for {payload.symbol} / {payload.frequency}")

        frame = pd.DataFrame(documents).sort_values("timestamp").reset_index(drop=True)
        if payload.source_field not in frame.columns:
            raise ValueError(f"Field {payload.source_field} not present in stock_kline data")

        persisted_records = 0
        results: List[IndicatorComputeResult] = []
        records_to_persist: List[IndicatorRecord] = []

        for item in payload.indicators:
            computed = self._compute_indicator(frame.copy(), item.name, item.params, payload.source_field)
            indicator_name = self._build_indicator_name(item.name, item.params)
            points: List[IndicatorSeriesPoint] = []

            for row in computed.to_dict(orient="records"):
                values = {
                    key: float(value)
                    for key, value in row.items()
                    if key != "timestamp" and value is not None and pd.notna(value)
                }
                if not values:
                    continue
                timestamp = row["timestamp"]
                points.append(IndicatorSeriesPoint(timestamp=timestamp, values=values))
                if payload.persist:
                    records_to_persist.append(
                        IndicatorRecord(
                            symbol=payload.symbol,
                            indicator=indicator_name,
                            timeframe=payload.frequency,
                            timestamp=timestamp,
                            value=next(iter(values.values())),
                            values=values,
                            payload={
                                "source_field": payload.source_field,
                                "params": item.params,
                            },
                            tags=["computed", item.name],
                        )
                    )

            results.append(
                IndicatorComputeResult(
                    symbol=payload.symbol,
                    frequency=payload.frequency,
                    indicator=indicator_name,
                    points=points,
                )
            )

        if records_to_persist:
            indicator_repository = self._get_indicator_repository(payload.target)
            await indicator_repository.ensure_indexes()
            stats = await indicator_repository.upsert_many(
                [
                    {
                        "symbol": record.symbol,
                        "indicator": record.indicator,
                        "timeframe": record.timeframe,
                        "timestamp": IndicatorRecord.normalize_timestamp(record.timestamp),
                        "value": record.value,
                        "values": record.values,
                        "payload": record.payload,
                        "tags": record.tags,
                        "provider": "backend_db_compute",
                    }
                    for record in records_to_persist
                ]
            )
            persisted_records = stats.get("upserted", 0) + stats.get("modified", 0)

        return IndicatorComputeResponse(
            symbol=payload.symbol,
            frequency=payload.frequency,
            source_field=payload.source_field,
            lookback=payload.lookback,
            results=results,
            persisted_records=persisted_records,
        )

    def _compute_indicator(
        self,
        frame: pd.DataFrame,
        name: str,
        params: Dict[str, float],
        source_field: str,
    ) -> pd.DataFrame:
        series = frame[source_field].astype(float)
        result = pd.DataFrame({"timestamp": frame["timestamp"]})

        if name == "sma":
            period = int(params.get("period", 20))
            result[f"sma_{period}"] = series.rolling(window=period, min_periods=period).mean()
            return result

        if name == "ema":
            period = int(params.get("period", 20))
            result[f"ema_{period}"] = series.ewm(span=period, adjust=False).mean()
            return result

        if name == "rsi":
            period = int(params.get("period", 14))
            delta = series.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, pd.NA)
            result[f"rsi_{period}"] = 100 - (100 / (1 + rs))
            return result

        if name == "macd":
            fast = int(params.get("fast", 12))
            slow = int(params.get("slow", 26))
            signal = int(params.get("signal", 9))
            fast_line = series.ewm(span=fast, adjust=False).mean()
            slow_line = series.ewm(span=slow, adjust=False).mean()
            macd_line = fast_line - slow_line
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            result["macd"] = macd_line
            result["signal"] = signal_line
            result["histogram"] = histogram
            return result

        raise ValueError(f"Unsupported indicator: {name}")

    @staticmethod
    def _build_indicator_name(name: str, params: Dict[str, float]) -> str:
        if not params:
            return name
        serialized = "_".join(f"{key}{int(value) if float(value).is_integer() else value}" for key, value in sorted(params.items()))
        return f"{name}_{serialized}"

    def _get_kline_repository(self, target: str) -> StockKlineRepository:
        key = target or "primary"
        if key not in self._kline_repositories:
            collection = self.registry.get_collection("stock_kline", key)
            self._kline_repositories[key] = StockKlineRepository(collection=collection)
        return self._kline_repositories[key]

    def _get_indicator_repository(self, target: str) -> IndicatorDataRepository:
        key = target or "primary"
        if key in self._indicator_repositories:
            return self._indicator_repositories[key]
        if key == "primary" and self._default_indicator_repository:
            self._indicator_repositories[key] = self._default_indicator_repository
            return self._default_indicator_repository
        collection = self.registry.get_collection("indicator", key)
        repository = IndicatorDataRepository(collection=collection)
        self._indicator_repositories[key] = repository
        return repository
