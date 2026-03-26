import datetime
from typing import List, Optional

from app.models.subscription import StrategySubscriptionState
from app.services.collection_service import BaseCollectionService
from app.services.portfolio_service import PortfolioService


class StrategySubscriptionService(BaseCollectionService):
    DEFAULT_STATE = {
        "strategies": [
            {
                "id": "alpha-trend",
                "name": "Alpha 趋势跟踪",
                "summary": "捕捉高胜率趋势行情，聚焦放量突破与动量修复信号",
                "riskLevel": "中",
                "signalFrequency": "日内/收盘",
                "lastSignal": "2025-01-15 10:12",
                "performance": 12.4,
                "subscribed": True,
                "channels": ["email"],
                "tags": ["趋势", "风控联动"],
                "subscribers": 86,
            }
        ],
        "blacklist": ["600519", "000001", "300750"],
    }

    def __init__(self, portfolio_service: Optional[PortfolioService] = None) -> None:
        super().__init__("strategy_subscriptions")
        self.portfolio_service = portfolio_service or PortfolioService()

    async def get_state(self, username: str) -> StrategySubscriptionState:
        await self._ensure_seeded(username)
        document = await self.collection.find_one({"username": username})
        state = (document or {}).get("state") or self.DEFAULT_STATE
        portfolio = await self.portfolio_service.get_overview()
        active_strategies = [item for item in portfolio.strategies if item.status == "active"]
        existing = {item["id"]: item for item in state.get("strategies", [])}

        merged = []
        for strategy in active_strategies:
            if strategy.id in existing:
                merged.append(existing[strategy.id])
            else:
                merged.append(
                    {
                        "id": strategy.id,
                        "name": strategy.name,
                        "summary": strategy.description or "基于数据库行情和指标的综合策略",
                        "riskLevel": "中",
                        "signalFrequency": "日内/收盘",
                        "lastSignal": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                        "performance": 0.0,
                        "subscribed": False,
                        "channels": ["email"],
                        "tags": ["系统推荐"],
                        "subscribers": 1,
                    }
                )

        state["strategies"] = merged
        return StrategySubscriptionState.parse_obj(state)

    async def set_subscribed(
        self,
        username: str,
        strategy_id: str,
        subscribed: bool,
        channels: Optional[List[str]],
    ) -> None:
        state = await self.get_state(username)
        updated = []
        for item in state.strategies:
            if item.id == strategy_id:
                item.subscribed = subscribed
                if channels is not None:
                    item.channels = channels
            updated.append(item)
        state.strategies = updated
        await self.collection.update_one(
            {"username": username},
            {"$set": {"state": state.dict(), "updated_at": datetime.datetime.utcnow()}},
            upsert=True,
        )

    async def update_blacklist(self, username: str, blacklist: List[str]) -> None:
        state = await self.get_state(username)
        state.blacklist = blacklist
        await self.collection.update_one(
            {"username": username},
            {"$set": {"state": state.dict(), "updated_at": datetime.datetime.utcnow()}},
            upsert=True,
        )

    async def _ensure_seeded(self, username: str) -> None:
        existing = await self.collection.find_one({"username": username})
        if existing:
            return
        await self.collection.insert_one(
            {
                "username": username,
                "state": self.DEFAULT_STATE,
                "updated_at": datetime.datetime.utcnow(),
            }
        )
