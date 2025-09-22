from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .base import IndicatorResult, registry


class MovingAverageIndicator:
    name = "MA"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        window = max(int(params.get("window", 5)), 1)
        closes = [float(bar["close"]) for bar in bars]
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        results: List[IndicatorResult] = []
        for idx, _ in enumerate(closes):
            start = max(0, idx - window + 1)
            window_values = closes[start : idx + 1]
            avg = sum(window_values) / len(window_values)
            results.append(IndicatorResult(date=dates[idx], value=avg))
        return results


registry.register(MovingAverageIndicator())


__all__ = ["MovingAverageIndicator"]
