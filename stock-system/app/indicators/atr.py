from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .base import IndicatorResult, registry


class ATRIndicator:
    name = "ATR"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        period = max(int(params.get("window", 14)), 1)
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        highs = [float(bar["high"]) for bar in bars]
        lows = [float(bar["low"]) for bar in bars]
        closes = [float(bar["close"]) for bar in bars]
        true_ranges: List[float] = []
        for idx in range(len(bars)):
            if idx == 0:
                true_range = highs[idx] - lows[idx]
            else:
                prev_close = closes[idx - 1]
                true_range = max(
                    highs[idx] - lows[idx],
                    abs(highs[idx] - prev_close),
                    abs(lows[idx] - prev_close),
                )
            true_ranges.append(true_range)
        atr_values: List[float] = []
        for idx, _ in enumerate(true_ranges):
            start = max(0, idx - period + 1)
            window = true_ranges[start : idx + 1]
            atr_values.append(sum(window) / len(window))
        return [IndicatorResult(date=dates[idx], value=atr_values[idx]) for idx in range(len(atr_values))]


registry.register(ATRIndicator())


__all__ = ["ATRIndicator"]
