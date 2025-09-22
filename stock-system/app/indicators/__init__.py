from __future__ import annotations

# Ensure builtin indicators are registered when the package is imported
from . import atr, boll, ma, macd, rsi  # noqa: F401

__all__ = ["atr", "boll", "ma", "macd", "rsi"]
