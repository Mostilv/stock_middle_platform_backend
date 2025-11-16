from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.data_sinks import DataSinkRegistry, data_sink_registry
from app.models.analytics import IndustryMetricResponse, IndustryMetricSeries
from app.repositories.indicator_repository import IndicatorDataRepository


class IndustryAnalyticsService:
    """Query helper that converts indicator records into industry time-series."""

    def __init__(self, registry: Optional[DataSinkRegistry] = None) -> None:
        self.registry = registry or data_sink_registry
        self._repositories: Dict[str, IndicatorDataRepository] = {}

    async def get_industry_metrics(
        self,
        indicator: str = "industry_metrics",
        *,
        target: str = "primary",
        timeframe: str = "1d",
        days: int = 12,
        end: Optional[datetime] = None,
    ) -> IndustryMetricResponse:
        repository = self._get_repository(target)
        bounded_days = max(1, min(days, 120))
        end_time = self._normalize_timestamp(end or datetime.utcnow())
        start_time = end_time - timedelta(days=bounded_days - 1)

        filters: Dict[str, object] = {
            "indicator": indicator.lower(),
            "timeframe": timeframe.lower(),
            "timestamp": {"$gte": start_time, "$lte": end_time},
        }

        # Fetch a generous amount of records to cover all industries.
        limit = bounded_days * 64
        records, _ = await repository.find_records(filters, skip=0, limit=limit)

        series_map: Dict[str, Dict[str, object]] = {}
        date_values: set[str] = set()

        for document in records:
            timestamp = document.get("timestamp")
            if not isinstance(timestamp, datetime):
                continue
            ts = self._normalize_timestamp(timestamp)
            date_label = ts.strftime("%Y-%m-%d")
            date_values.add(date_label)

            symbol = document.get("symbol", "")
            payload = document.get("payload") or {}
            values = document.get("values") or {}
            key = symbol or payload.get("industry_code", "")
            if not key:
                continue

            entry = series_map.setdefault(
                key,
                {
                    "symbol": symbol or f"INDUSTRY:{payload.get('industry_code', key)}",
                    "code": payload.get("industry_code") or key.split(":")[-1],
                    "name": payload.get("industry_name") or key,
                    "points": [],
                },
            )
            entry["points"].append(
                {
                    "date": ts,
                    "momentum": values.get("momentum"),
                    "width": values.get("width"),
                }
            )

        dates = sorted(date_values)[-bounded_days:]
        series = []
        for meta in series_map.values():
            points = [
                point
                for point in sorted(
                    meta["points"], key=lambda item: item["date"]
                )
                if point["date"].strftime("%Y-%m-%d") in dates
            ]
            series.append(
                IndustryMetricSeries(
                    symbol=meta["symbol"],
                    code=meta["code"],
                    name=meta["name"],
                    points=points,
                )
            )

        return IndustryMetricResponse(
            indicator=indicator,
            target=target,
            start=start_time,
            end=end_time,
            dates=dates,
            series=series,
        )

    def _get_repository(self, target: str) -> IndicatorDataRepository:
        key = target or "primary"
        if key not in self._repositories:
            collection = self.registry.get_collection("indicator", key)
            self._repositories[key] = IndicatorDataRepository(collection=collection)
        return self._repositories[key]

    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        if value.tzinfo:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
