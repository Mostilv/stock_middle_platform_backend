from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .base import IndicatorResult, registry


def _ema(values: List[float], span: int) -> List[float]:
    alpha = 2 / (span + 1)
    ema: List[float] = []
    for idx, value in enumerate(values):
        if idx == 0:
            ema.append(value)
        else:
            ema.append(alpha * value + (1 - alpha) * ema[-1])
    return ema


class MACDIndicator:
    name = "MACD"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
        closes = [float(bar["close"]) for bar in bars]
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        if not closes:
            return []
        ema_fast = _ema(closes, fast)
        ema_slow = _ema(closes, slow)
        macd_line = [fast_v - slow_v for fast_v, slow_v in zip(ema_fast, ema_slow)]
        signal_line = _ema(macd_line, signal)
        histogram = [macd - sig for macd, sig in zip(macd_line, signal_line)]
        return [IndicatorResult(date=dates[idx], value=histogram[idx]) for idx in range(len(histogram))]


registry.register(MACDIndicator())


__all__ = ["MACDIndicator"]
