from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, UpdateOne

from app.config import settings
from app.db.database import db_manager
from app.models.joinquant import JoinQuantWebhookPayload
from app.models.strategy import Strategy, StrategyPosition, StrategySignal
from app.services.strategy_service import StrategyService

logger = logging.getLogger(__name__)


class JoinQuantService:
    """处理聚宽信号推送与查询的服务"""

    _index_lock: asyncio.Lock = asyncio.Lock()
    _indexes_ready: bool = False

    def __init__(self, strategy_service: StrategyService) -> None:
        self.strategy_service = strategy_service
        self.signal_collection = db_manager.get_mongodb_collection("strategy_signals")
        self.position_collection = db_manager.get_mongodb_collection("strategy_positions")

    async def ensure_indexes(self) -> None:
        if self.__class__._indexes_ready:
            return

        async with self.__class__._index_lock:
            if self.__class__._indexes_ready:
                return

            await self.signal_collection.create_index(
                [("strategy_id", ASCENDING), ("triggered_at", DESCENDING)],
                background=True,
            )
            await self.signal_collection.create_index(
                [
                    ("strategy_id", ASCENDING),
                    ("batch_id", ASCENDING),
                    ("code", ASCENDING),
                    ("side", ASCENDING),
                ],
                background=True,
            )
            await self.position_collection.create_index(
                [("strategy_id", ASCENDING), ("as_of", DESCENDING)],
                background=True,
            )
            await self.position_collection.create_index(
                [
                    ("strategy_id", ASCENDING),
                    ("batch_id", ASCENDING),
                    ("code", ASCENDING),
                ],
                background=True,
            )

            self.__class__._indexes_ready = True
            logger.info("✅ JoinQuant 信号/持仓索引已创建")

    def verify_signature(
        self, signature: Optional[str], timestamp: Optional[str], body: bytes
    ) -> bool:
        """校验Webhook签名"""

        secret = settings.joinquant_webhook_secret
        if not secret:
            return True
        if not signature or not timestamp:
            return False

        try:
            payload = f"{timestamp}:{body.decode('utf-8')}".encode("utf-8")
        except UnicodeDecodeError:
            return False

        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def process_webhook(self, payload: JoinQuantWebhookPayload) -> Dict[str, Any]:
        """处理聚宽推送的调仓与持仓数据"""

        await self.ensure_indexes()

        strategy = await self._resolve_strategy(payload)
        if not strategy:
            raise ValueError("未找到对应策略，请确认strategy_id或strategy_code是否正确")

        timestamp = payload.sent_at or datetime.utcnow()
        batch_id = payload.batch_id or f"{strategy.id}-{int(timestamp.timestamp())}"
        source = payload.source or "joinquant"

        signal_ops = self._prepare_signal_operations(payload, strategy, timestamp, batch_id, source)
        position_ops = self._prepare_position_operations(payload, strategy, timestamp, batch_id, source)

        signal_count = 0
        position_count = 0

        if signal_ops:
            result = await self.signal_collection.bulk_write(signal_ops, ordered=False)
            signal_count = (result.upserted_count or 0) + (result.modified_count or 0)

        if position_ops:
            result = await self.position_collection.bulk_write(position_ops, ordered=False)
            position_count = (result.upserted_count or 0) + (result.modified_count or 0)

        update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow()}
        if signal_count:
            update_fields["last_signal_at"] = timestamp
        if position_count:
            update_fields["last_positions_at"] = timestamp

        if update_fields:
            await self.strategy_service.collection.update_one(
                {"_id": ObjectId(strategy.id)},
                {"$set": update_fields},
            )

        logger.info(
            "📡 聚宽信号已同步: strategy=%s signals=%s positions=%s batch=%s",
            strategy.id,
            signal_count,
            position_count,
            batch_id,
        )

        return {
            "strategy_id": strategy.id,
            "signals": signal_count,
            "positions": position_count,
            "batch_id": batch_id,
            "timestamp": timestamp,
        }

    async def list_signals(
        self,
        strategy_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
        side: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[StrategySignal]:
        """查询策略的调仓信号"""

        await self.ensure_indexes()

        query: Dict[str, Any] = {"strategy_id": strategy_id}
        if side:
            query["side"] = side.upper()
        if start or end:
            timerange: Dict[str, Any] = {}
            if start:
                timerange["$gte"] = start
            if end:
                timerange["$lte"] = end
            query["triggered_at"] = timerange

        cursor = (
            self.signal_collection.find(query)
            .sort("triggered_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        documents = await cursor.to_list(length=None)
        return [self._map_signal(doc) for doc in documents if doc]

    async def get_latest_positions(self, strategy_id: str) -> List[StrategyPosition]:
        """查询策略最新的持仓快照"""

        await self.ensure_indexes()

        latest = await (
            self.position_collection.find({"strategy_id": strategy_id})
            .sort("as_of", DESCENDING)
            .limit(1)
            .to_list(length=1)
        )
        if not latest:
            return []

        as_of = latest[0]["as_of"]
        cursor = (
            self.position_collection.find({"strategy_id": strategy_id, "as_of": as_of})
            .sort("code", ASCENDING)
        )
        documents = await cursor.to_list(length=None)
        return [self._map_position(doc) for doc in documents if doc]

    def _prepare_signal_operations(
        self,
        payload: JoinQuantWebhookPayload,
        strategy: Strategy,
        timestamp: datetime,
        batch_id: str,
        source: str,
    ) -> List[UpdateOne]:
        operations: List[UpdateOne] = []
        now = datetime.utcnow()
        base_metadata = self._collect_base_metadata(payload)

        for item in payload.orders or []:
            record = self._normalize_order(item, strategy, timestamp, batch_id, source, now, base_metadata)
            if not record:
                continue
            operations.append(
                UpdateOne(
                    {
                        "strategy_id": record["strategy_id"],
                        "code": record["code"],
                        "side": record["side"],
                        "triggered_at": record["triggered_at"],
                        "batch_id": record["batch_id"],
                    },
                    {
                        "$set": {k: v for k, v in record.items() if k not in {"created_at"}},
                        "$setOnInsert": {"created_at": record["created_at"]},
                        "$currentDate": {"updated_at": True},
                    },
                    upsert=True,
                )
            )
        return operations

    def _prepare_position_operations(
        self,
        payload: JoinQuantWebhookPayload,
        strategy: Strategy,
        timestamp: datetime,
        batch_id: str,
        source: str,
    ) -> List[UpdateOne]:
        operations: List[UpdateOne] = []
        now = datetime.utcnow()
        base_metadata = self._collect_base_metadata(payload)

        for item in payload.positions or []:
            record = self._normalize_position(item, strategy, timestamp, batch_id, source, now, base_metadata)
            if not record:
                continue
            operations.append(
                UpdateOne(
                    {
                        "strategy_id": record["strategy_id"],
                        "code": record["code"],
                        "as_of": record["as_of"],
                        "batch_id": record["batch_id"],
                    },
                    {
                        "$set": {k: v for k, v in record.items() if k not in {"created_at"}},
                        "$setOnInsert": {"created_at": record["created_at"]},
                        "$currentDate": {"updated_at": True},
                    },
                    upsert=True,
                )
            )
        return operations

    async def _resolve_strategy(self, payload: JoinQuantWebhookPayload) -> Optional[Strategy]:
        if payload.strategy_id:
            strategy = await self.strategy_service.get_strategy_by_id(payload.strategy_id)
            if strategy:
                return strategy
        if payload.strategy_code:
            return await self.strategy_service.get_strategy_by_external_id(
                payload.strategy_code, payload.source or "joinquant"
            )
        return None

    def _collect_base_metadata(self, payload: JoinQuantWebhookPayload) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        if payload.note:
            metadata["note"] = payload.note
        metadata.update(payload.metadata or {})
        return metadata

    def _normalize_order(
        self,
        item: Dict[str, Any],
        strategy: Strategy,
        timestamp: datetime,
        batch_id: str,
        source: str,
        now: datetime,
        base_metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        code = item.get("code") or item.get("symbol")
        if not code:
            return None

        side = (item.get("side") or item.get("action") or "UNKNOWN").upper()
        quantity = self._to_float(
            item.get("qty") or item.get("quantity") or item.get("volume")
        )
        price = self._to_float(item.get("price") or item.get("avg_cost"))
        signal_type = item.get("signal_type") or base_metadata.get("signal_type") or "rebalance"

        metadata = dict(base_metadata)
        if isinstance(item.get("meta"), dict):
            metadata.update(item["meta"])

        note = item.get("note") or item.get("reason")
        if note:
            metadata.setdefault("order_note", note)

        record = {
            "strategy_id": strategy.id,
            "external_strategy_id": strategy.external_id,
            "code": code,
            "side": side,
            "quantity": quantity,
            "price": price,
            "signal_type": signal_type,
            "triggered_at": timestamp,
            "batch_id": batch_id,
            "source": source,
            "note": note,
            "metadata": metadata,
            "raw": item,
            "created_at": now,
        }
        return record

    def _normalize_position(
        self,
        item: Dict[str, Any],
        strategy: Strategy,
        timestamp: datetime,
        batch_id: str,
        source: str,
        now: datetime,
        base_metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        code = item.get("code") or item.get("symbol")
        if not code:
            return None

        qty = self._to_float(item.get("qty") or item.get("quantity") or item.get("volume"))
        weight = self._to_optional_float(item.get("weight"))
        price = self._to_optional_float(item.get("price") or item.get("avg_cost"))
        market_value = self._to_optional_float(
            item.get("market_value") or item.get("value")
        )
        as_of = self._parse_datetime(item.get("as_of")) or timestamp

        metadata = dict(base_metadata)
        if isinstance(item.get("meta"), dict):
            metadata.update(item["meta"])

        record = {
            "strategy_id": strategy.id,
            "external_strategy_id": strategy.external_id,
            "code": code,
            "quantity": qty,
            "weight": weight,
            "price": price,
            "market_value": market_value,
            "as_of": as_of,
            "batch_id": batch_id,
            "source": source,
            "metadata": metadata,
            "raw": item,
            "created_at": now,
        }
        return record

    def _map_signal(self, document: Dict[str, Any]) -> StrategySignal:
        data = dict(document)
        data["id"] = str(data.pop("_id"))
        data.pop("raw", None)
        data.setdefault("metadata", {})
        data.setdefault("signal_type", "rebalance")
        data.setdefault("note", None)
        data.setdefault("source", "joinquant")
        data.setdefault("external_strategy_id", None)
        data.setdefault("quantity", self._to_float(data.get("quantity")))
        data.setdefault("price", self._to_float(data.get("price")))
        data.setdefault("created_at", data.get("triggered_at", datetime.utcnow()))
        data.setdefault("updated_at", data.get("created_at"))
        data["side"] = (data.get("side") or "UNKNOWN").upper()
        return StrategySignal(**data)

    def _map_position(self, document: Dict[str, Any]) -> StrategyPosition:
        data = dict(document)
        data["id"] = str(data.pop("_id"))
        data.pop("raw", None)
        data.setdefault("metadata", {})
        data.setdefault("source", "joinquant")
        data.setdefault("external_strategy_id", None)
        data.setdefault("quantity", self._to_float(data.get("quantity")))
        data.setdefault("weight", self._to_optional_float(data.get("weight")))
        data.setdefault("price", self._to_optional_float(data.get("price")))
        data.setdefault("market_value", self._to_optional_float(data.get("market_value")))
        data.setdefault("created_at", data.get("as_of", datetime.utcnow()))
        data.setdefault("updated_at", data.get("created_at"))
        return StrategyPosition(**data)

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_optional_float(value: Any) -> Optional[float]:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (OSError, ValueError):
                return None
        if isinstance(value, str):
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None


__all__ = ["JoinQuantService"]
