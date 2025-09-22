from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List

from .base import IndicatorResult, registry


class BollingerIndicator:
    name = "BOLL"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        window = max(int(params.get("window", 20)), 1)
        num_std = float(params.get("num_std", 2))
        closes = [float(bar["close"]) for bar in bars]
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        results: List[IndicatorResult] = []
        for idx in range(len(closes)):
            start = max(0, idx - window + 1)
            window_values = closes[start : idx + 1]
            mean = sum(window_values) / len(window_values)
            variance = sum((value - mean) ** 2 for value in window_values) / len(window_values)
            std = math.sqrt(variance)
            middle = mean
            results.append(IndicatorResult(date=dates[idx], value=middle))
        return results


registry.register(BollingerIndicator())


__all__ = ["BollingerIndicator"]
