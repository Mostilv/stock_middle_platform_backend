from __future__ import annotations

import asyncio
from datetime import date, timedelta

from app.repo.mongo import kline_repo
from app.repo.mysql import base as mysql_base
from app.repo.mysql import positions_repo, rebalance_repo, signals_repo
from app.service.indicator_service import IndicatorService


async def seed_mysql() -> None:
    session_factory = mysql_base.get_sessionmaker()
    async with session_factory() as session:
        await positions_repo.save_positions(
            session,
            [
                {
                    "code": "600519",
                    "qty": 100,
                    "weight": 0.2,
                    "avg_cost": 1500,
                    "market_value": 150000,
                    "source": "seed",
                },
                {
                    "code": "000001",
                    "qty": 1000,
                    "weight": 0.1,
                    "avg_cost": 12,
                    "market_value": 12000,
                    "source": "seed",
                },
            ],
        )
        await signals_repo.insert_signals(
            session,
            [
                {
                    "code": "600519",
                    "side": "BUY",
                    "qty": 10,
                    "price": 1500,
                    "reason": "init",
                    "source": "seed",
                }
            ],
        )
        await rebalance_repo.create_plan(
            session,
            date.today(),
            {"600519": 0.2, "000001": 0.1},
            {"impact": "low"},
            "Initial plan",
        )


async def seed_mongo() -> None:
    today = date.today()
    bars = []
    for idx in range(30):
        day = today - timedelta(days=idx)
        bars.append(
            {
                "date": day.isoformat(),
                "open": 1500 + idx,
                "high": 1510 + idx,
                "low": 1490 + idx,
                "close": 1505 + idx,
                "volume": 1_000_000 + idx * 1000,
                "turnover": 10_000_000 + idx * 1000,
            }
        )
    await kline_repo.upsert_bars("600519", "daily", "qfq", bars)
    await kline_repo.upsert_bars("000001", "daily", "qfq", bars)


async def seed_indicators() -> None:
    service = IndicatorService()
    await service.compute_builtin("600519", "MA", {"window": 5})
    await service.compute_builtin("600519", "RSI", {"window": 14})


async def main() -> None:
    await seed_mysql()
    await seed_mongo()
    await seed_indicators()


if __name__ == "__main__":
    asyncio.run(main())
