from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Protocol


@dataclass
class IndicatorResult:
    """Result item for an indicator computation."""

    date: datetime
    value: float


class Indicator(Protocol):
    name: str

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        ...


class IndicatorRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Indicator] = {}

    def register(self, indicator: Indicator) -> None:
        self._registry[indicator.name.upper()] = indicator

    def get(self, name: str) -> Indicator:
        key = name.upper()
        if key not in self._registry:
            raise KeyError(f"Indicator {name} not registered")
        return self._registry[key]

    def list_names(self) -> List[str]:
        return sorted(self._registry.keys())


registry = IndicatorRegistry()


__all__ = ["Indicator", "IndicatorResult", "registry", "IndicatorRegistry"]
