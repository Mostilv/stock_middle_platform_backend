from typing import Dict, Optional

from app.models.qlib import QlibIngestSummary, QlibStockBatch, QlibStockRecord
from app.repositories.qlib_data_repository import QlibStockDataRepository


class QlibDataIngestionService:
    """Business logic for accepting qlib-formatted stock bars from external systems."""

    def __init__(
        self, repository: Optional[QlibStockDataRepository] = None
    ) -> None:
        self.repository = repository or QlibStockDataRepository()

    async def ingest_batch(self, batch: QlibStockBatch) -> QlibIngestSummary:
        await self.repository.ensure_indexes()
        documents = [self._record_to_document(batch, record) for record in batch.records]
        stats = await self.repository.upsert_many(documents)
        return QlibIngestSummary(
            total=len(documents),
            matched=stats.get("matched", 0),
            modified=stats.get("modified", 0),
            upserted=stats.get("upserted", 0),
        )

    def _record_to_document(
        self, batch: QlibStockBatch, record: QlibStockRecord
    ) -> Dict[str, object]:
        document: Dict[str, object] = {
            "instrument": record.instrument,
            "freq": record.freq,
            "datetime": QlibStockRecord.normalize_datetime(record.datetime),
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
            "amount": record.amount,
            "factor": record.factor,
            "vwap": record.vwap,
            "turnover": record.turnover,
            "limit_status": record.limit_status,
            "suspended": record.suspended,
            "provider": batch.provider,
            "market": batch.market,
            "source_timezone": batch.timezone,
        }

        # Remove None so Mongo documents stay tidy.
        document = {key: value for key, value in document.items() if value is not None}

        if record.extra_fields:
            document.update(record.extra_fields)

        return document
