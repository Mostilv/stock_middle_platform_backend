from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..base import IndicatorResult


class MomentumV1:
    name = "MOMENTUM_V1"

    async def compute(
        self,
        code: str,
        bars: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[IndicatorResult]:
        period = max(int(params.get("period", 20)), 1)
        closes = [float(bar["close"]) for bar in bars]
        dates = [datetime.fromisoformat(bar["date"]) for bar in bars]
        results: List[IndicatorResult] = []
        for idx, close in enumerate(closes):
            if idx < period:
                momentum = 0.0
            else:
                prev = closes[idx - period]
                momentum = (close - prev) / prev if prev else 0.0
            results.append(IndicatorResult(date=dates[idx], value=momentum))
        return results


__all__ = ["MomentumV1"]
