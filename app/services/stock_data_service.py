from datetime import date, datetime
from typing import Dict, List, Optional

from app.core.data_sinks import DataSinkRegistry, data_sink_registry
from app.models.indicator import IndicatorPushRequest
from app.models.stock_data import (
    DataPushConfigResponse,
    DataSinkTargetInfo,
    DataWriteSummary,
    StockBasicBatch,
    StockBasicRecord,
    StockKlineBatch,
    StockKlineRecord,
)
from app.repositories.stock_basic_repository import StockBasicRepository
from app.repositories.stock_kline_repository import StockKlineRepository


class StockDataService:
    """Business logic around pushing stock basics and K-line data."""

    def __init__(self, registry: Optional[DataSinkRegistry] = None) -> None:
        self.registry = registry or data_sink_registry
        self._basic_repositories: Dict[str, StockBasicRepository] = {}
        self._kline_repositories: Dict[str, StockKlineRepository] = {}

    def describe_targets(self) -> DataPushConfigResponse:
        datasets = {
            dataset: [
                DataSinkTargetInfo(
                    dataset=dataset,
                    target=sink.target,
                    database=sink.database,
                    collection=sink.collection,
                    description=sink.description,
                )
                for sink in sinks
            ]
            for dataset, sinks in self.registry.list_datasets().items()
            if dataset in {"stock_basic", "stock_kline", "indicator"}
        }
        schemas = {
            "stock_basic": StockBasicBatch.schema(),
            "stock_kline": StockKlineBatch.schema(),
            "indicator": IndicatorPushRequest.schema(),
        }
        return DataPushConfigResponse(datasets=datasets, schemas=schemas)

    async def ingest_basic(self, payload: StockBasicBatch) -> DataWriteSummary:
        repository = self._get_basic_repository(payload.target)
        await repository.ensure_indexes()
        documents = [
            self._basic_record_to_document(payload.provider, record)
            for record in payload.items
        ]
        stats = await repository.upsert_many(documents)
        return DataWriteSummary(
            total=len(documents),
            matched=stats.get("matched", 0),
            modified=stats.get("modified", 0),
            upserted=stats.get("upserted", 0),
        )

    async def ingest_kline(self, payload: StockKlineBatch) -> DataWriteSummary:
        repository = self._get_kline_repository(payload.target)
        await repository.ensure_indexes()
        documents = [
            self._kline_record_to_document(payload.provider, record)
            for record in payload.items
        ]
        stats = await repository.upsert_many(documents)
        return DataWriteSummary(
            total=len(documents),
            matched=stats.get("matched", 0),
            modified=stats.get("modified", 0),
            upserted=stats.get("upserted", 0),
        )

    def _get_basic_repository(self, target: str) -> StockBasicRepository:
        key = target or "primary"
        if key not in self._basic_repositories:
            collection = self.registry.get_collection("stock_basic", key)
            self._basic_repositories[key] = StockBasicRepository(collection=collection)
        return self._basic_repositories[key]

    def _get_kline_repository(self, target: str) -> StockKlineRepository:
        key = target or "primary"
        if key not in self._kline_repositories:
            collection = self.registry.get_collection("stock_kline", key)
            self._kline_repositories[key] = StockKlineRepository(collection=collection)
        return self._kline_repositories[key]

    def _basic_record_to_document(
        self, provider: str, record: StockBasicRecord
    ) -> Dict[str, object]:
        payload = {
            "symbol": record.symbol,
            "name": record.name,
            "exchange": record.exchange,
            "list_date": self._date_to_datetime(record.list_date),
            "delist_date": self._date_to_datetime(record.delist_date),
            "status": record.status,
            "type": record.type,
            "market": record.market,
            "industry": record.industry,
            "area": record.area,
            "currency": record.currency,
            "provider": provider,
            "payload": record.payload or {},
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _kline_record_to_document(
        self, provider: str, record: StockKlineRecord
    ) -> Dict[str, object]:
        timestamp = record.timestamp.replace(tzinfo=None)
        payload = {
            "symbol": record.symbol,
            "frequency": record.frequency,
            "timestamp": timestamp,
            "trade_date": timestamp.date(),
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
            "amount": record.amount,
            "turnover_rate": record.turnover_rate,
            "adjust_flag": record.adjust_flag,
            "trade_status": record.trade_status,
            "pct_change": record.pct_change,
            "pe_ttm": record.pe_ttm,
            "pb_mrq": record.pb_mrq,
            "ps_ttm": record.ps_ttm,
            "pcf_ncf_ttm": record.pcf_ncf_ttm,
            "provider": provider,
            "payload": record.payload or {},
        }
        return {key: value for key, value in payload.items() if value is not None}

    @staticmethod
    def _date_to_datetime(value: Optional[date]) -> Optional[datetime]:
        if value is None:
            return None
        return datetime(value.year, value.month, value.day)
