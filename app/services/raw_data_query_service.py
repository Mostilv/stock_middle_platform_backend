from datetime import datetime
from typing import Dict, List, Optional

from app.core.data_sinks import DataSinkRegistry, data_sink_registry
from app.repositories.stock_basic_repository import StockBasicRepository
from app.repositories.stock_kline_repository import StockKlineRepository


class RawStockDataQueryService:
    def __init__(self, registry: Optional[DataSinkRegistry] = None) -> None:
        self.registry = registry or data_sink_registry
        self._basic_repositories: Dict[str, StockBasicRepository] = {}
        self._kline_repositories: Dict[str, StockKlineRepository] = {}

    async def list_stock_basics(
        self,
        *,
        target: str = "primary",
        symbol: Optional[str] = None,
        industry: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        repository = self._get_basic_repository(target)
        records = await repository.find_records(
            symbol=symbol.upper() if symbol else None,
            industry=industry,
            exchange=exchange.upper() if exchange else None,
            limit=limit,
        )
        return [self._serialize_document(item) for item in records]

    async def list_stock_kline(
        self,
        *,
        target: str = "primary",
        symbol: str,
        frequency: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 200,
    ) -> List[Dict]:
        repository = self._get_kline_repository(target)
        records = await repository.find_symbol_records(
            symbol=symbol.upper(),
            frequency=frequency.lower(),
            start=start,
            end=end,
            limit=limit,
            descending=False,
        )
        return [self._serialize_document(item) for item in records]

    async def list_basic_symbols(
        self,
        *,
        target: str = "primary",
        limit: int = 200,
    ) -> List[str]:
        repository = self._get_basic_repository(target)
        return await repository.list_symbols(limit=limit)

    async def list_kline_symbols(
        self,
        *,
        target: str = "primary",
        frequency: Optional[str] = None,
        limit: int = 200,
    ) -> List[str]:
        repository = self._get_kline_repository(target)
        return await repository.list_symbols(
            frequency=frequency.lower() if frequency else None,
            limit=limit,
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

    @staticmethod
    def _serialize_document(document: Dict) -> Dict:
        payload = dict(document)
        if "_id" in payload:
            payload["id"] = str(payload.pop("_id"))
        return payload
