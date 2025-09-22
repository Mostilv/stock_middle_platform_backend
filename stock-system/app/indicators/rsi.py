from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .base import IndicatorResult, registry


class RSIIndicator:
    name = "RSI"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        period = max(int(params.get("window", 14)), 1)
        closes = [float(bar["close"]) for bar in bars]
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        results: List[IndicatorResult] = []
        gains = [0.0]
        losses = [0.0]
        for idx in range(1, len(closes)):
            change = closes[idx] - closes[idx - 1]
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))
        for idx, date in enumerate(dates):
            if idx == 0:
                results.append(IndicatorResult(date=date, value=50.0))
                continue
            start = max(1, idx - period + 1)
            avg_gain = sum(gains[start: idx + 1]) / min(period, idx)
            avg_loss = sum(losses[start: idx + 1]) / min(period, idx)
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            results.append(IndicatorResult(date=date, value=rsi))
        return results


registry.register(RSIIndicator())


__all__ = ["RSIIndicator"]
