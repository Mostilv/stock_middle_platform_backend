from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.data_sinks import DataSinkRegistry, data_sink_registry
from app.models.indicator import (
    IndicatorPushRequest,
    IndicatorQueryItem,
    IndicatorQueryResponse,
    IndicatorRecord,
    IndicatorWriteSummary,
)
from app.repositories.indicator_repository import IndicatorDataRepository


class IndicatorService:
    """指标数据写入与查询服务"""

    DEFAULT_LIMIT = 100
    MAX_LIMIT = 500

    def __init__(
        self,
        repository: Optional[IndicatorDataRepository] = None,
        registry: Optional[DataSinkRegistry] = None,
    ) -> None:
        self.registry = registry or data_sink_registry
        self._default_repository = repository
        self._repositories: Dict[str, IndicatorDataRepository] = {}

    async def ingest(self, payload: IndicatorPushRequest) -> IndicatorWriteSummary:
        """写入外部推送的指标数据"""
        repository = self._get_repository(payload.target)
        await repository.ensure_indexes()
        documents = [
            self._record_to_document(payload.provider, record)
            for record in payload.records
        ]
        stats = await repository.upsert_many(documents)
        return IndicatorWriteSummary(
            total=len(documents),
            matched=stats.get("matched", 0),
            modified=stats.get("modified", 0),
            upserted=stats.get("upserted", 0),
        )

    async def query(
        self,
        indicator: str,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        tags: Optional[List[str]] = None,
        target: str = "primary",
    ) -> IndicatorQueryResponse:
        """根据条件查询指标结果"""
        if not indicator:
            raise ValueError("indicator 为必填参数")

        filters: Dict[str, Any] = {"indicator": indicator.strip().lower()}

        if symbol:
            filters["symbol"] = symbol.strip().upper()

        if timeframe:
            filters["timeframe"] = timeframe.strip().lower()

        ts_filters: Dict[str, datetime] = {}
        if start:
            ts_filters["$gte"] = self._normalize_timestamp(start)
        if end:
            ts_filters["$lte"] = self._normalize_timestamp(end)
        if ts_filters:
            filters["timestamp"] = ts_filters

        if tags:
            normalized_tags = [tag.strip().lower() for tag in tags if tag.strip()]
            if normalized_tags:
                filters["tags"] = {"$all": normalized_tags}

        safe_limit = self._normalize_limit(limit)
        safe_skip = self._normalize_skip(skip)

        repository = self._get_repository(target)
        records, total = await repository.find_records(
            filters, safe_skip, safe_limit
        )
        items = [self._document_to_model(document) for document in records]
        return IndicatorQueryResponse(total=total, data=items)

    def _record_to_document(
        self, provider: str, record: IndicatorRecord
    ) -> Dict[str, Any]:
        timestamp = IndicatorRecord.normalize_timestamp(record.timestamp)
        tags = sorted(set(record.tags))
        return {
            "indicator": record.indicator,
            "symbol": record.symbol,
            "timeframe": record.timeframe,
            "timestamp": timestamp,
            "value": record.value,
            "values": record.values,
            "payload": record.payload,
            "tags": tags,
            "provider": provider,
        }

    def _document_to_model(self, document: Dict[str, Any]) -> IndicatorQueryItem:
        payload = dict(document)
        if "_id" in payload:
            payload["id"] = str(payload.pop("_id"))
        payload.setdefault("tags", [])
        payload.setdefault("values", {})
        payload.setdefault("payload", {})
        return IndicatorQueryItem(**payload)

    @staticmethod
    def _normalize_limit(value: Optional[int]) -> int:
        if value is None:
            return IndicatorService.DEFAULT_LIMIT
        return max(1, min(value, IndicatorService.MAX_LIMIT))

    @staticmethod
    def _normalize_skip(value: Optional[int]) -> int:
        if value is None:
            return 0
        return max(0, value)

    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        return IndicatorRecord.normalize_timestamp(value)

    def _get_repository(self, target: Optional[str]) -> IndicatorDataRepository:
        key = (target or "primary").lower()
        if key in self._repositories:
            return self._repositories[key]

        if key == "primary" and self._default_repository:
            self._repositories[key] = self._default_repository
            return self._default_repository

        collection = self.registry.get_collection("indicator", key)
        repository = IndicatorDataRepository(collection=collection)
        self._repositories[key] = repository
        return repository
