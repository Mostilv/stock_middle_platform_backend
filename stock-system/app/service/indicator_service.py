from __future__ import annotations

import importlib
from datetime import date
from typing import Any, Dict, Iterable

from .. import indicators  # noqa: F401  # ensure builtin indicators are registered
from ..indicators.base import registry
from ..repo.mongo import indicators_repo, kline_repo
from ..repo.mysql import indicator_defs_repo


class IndicatorService:
    def __init__(self) -> None:
        self.period = "daily"
        self.adjust = "qfq"

    async def compute_builtin(
        self,
        code: str,
        indicator_name: str,
        params: Dict[str, Any],
        start: date | None = None,
        end: date | None = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        bars = await kline_repo.query_bars(code, self.period, start, end, self.adjust, limit)
        indicator = registry.get(indicator_name)
        results = await indicator.compute(code, bars, params)
        inserted = await indicators_repo.upsert_indicator_series(
            code,
            indicator_name,
            params,
            [
                {"date": item.date, "value": item.value}
                for item in results
            ],
        )
        return {"code": code, "indicator": indicator_name, "inserted": inserted}

    async def define_custom_indicator(
        self,
        session: Any,
        name: str,
        description: str,
        params_schema: Dict[str, Any],
        impl_ref: str,
    ) -> Dict[str, Any]:
        record = await indicator_defs_repo.create_or_update(
            session,
            name,
            description,
            params_schema,
            impl_ref,
        )
        return {
            "id": record.id,
            "name": record.name,
            "description": record.description,
            "impl_ref": record.impl_ref,
        }

    async def _load_custom_indicator(self, impl_ref: str):
        module_name, _, class_name = impl_ref.rpartition(".")
        if not module_name:
            module_name = impl_ref
            class_name = "Indicator"
        module = importlib.import_module(module_name)
        candidate_names = [class_name, "Indicator", "MomentumV1", "CustomIndicator"]
        for name in candidate_names:
            if hasattr(module, name):
                klass = getattr(module, name)
                return klass()
        raise AttributeError(f"Module {module_name} does not expose a known indicator class")

    async def compute_custom_indicator(
        self,
        session: Any,
        codes: Iterable[str],
        indicator_name: str,
        params: Dict[str, Any],
        start: str | None,
        end: str | None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        record = await indicator_defs_repo.get_by_name(session, indicator_name)
        if record is None:
            raise ValueError(f"Indicator {indicator_name} not defined")
        indicator_impl = await self._load_custom_indicator(record.impl_ref)
        start_date = date.fromisoformat(start) if start else None
        end_date = date.fromisoformat(end) if end else None
        summary = {"inserted": 0, "updated": 0, "errors": 0}
        for code in codes:
            bars = await kline_repo.query_bars(code, self.period, start_date, end_date, self.adjust, limit)
            results = await indicator_impl.compute(code, bars, params)
            inserted = await indicators_repo.upsert_indicator_series(
                code,
                indicator_name,
                params,
                [
                    {"date": item.date, "value": item.value}
                    for item in results
                ],
            )
            summary["inserted"] += inserted
        return summary

    async def query_indicator(
        self,
        code: str,
        indicator_name: str,
        start: str | None,
        end: str | None,
        limit: int = 200,
    ) -> Dict[str, Any]:
        docs = await indicators_repo.query_indicator_series(code, indicator_name, start, end, limit)
        return {
            "code": code,
            "indicator": indicator_name,
            "series": docs,
            "next_cursor": None,
        }


__all__ = ["IndicatorService"]
