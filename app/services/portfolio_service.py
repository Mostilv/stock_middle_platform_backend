import datetime

from app.models.portfolio import PortfolioOverview
from app.services.collection_service import BaseCollectionService


class PortfolioService(BaseCollectionService):
    DEFAULT_OVERVIEW = {
        "strategies": [
            {
                "id": "1",
                "name": "价值投资策略",
                "description": "基于基本面分析的价值投资策略",
                "status": "active",
                "totalValue": 1_000_000,
                "totalWeight": 100,
                "items": [
                    {
                        "key": "1",
                        "stock": "贵州茅台",
                        "code": "600519",
                        "currentWeight": 15.2,
                        "targetWeight": 18,
                        "action": "buy",
                        "price": 1688,
                        "quantity": 100,
                        "status": "pending",
                        "createdAt": "2024-01-15",
                        "marketValue": 168800,
                    }
                ],
                "createdAt": "2024-01-01",
            }
        ],
        "todayPnL": 12500,
        "totalPnL": 89000,
        "todayRebalance": 8,
        "todayPendingRebalance": 3,
    }

    def __init__(self) -> None:
        super().__init__("portfolio_overview")

    async def get_overview(self) -> PortfolioOverview:
        await self._ensure_seeded()
        document = await self.collection.find_one({}) or self.DEFAULT_OVERVIEW
        return PortfolioOverview.parse_obj(self.strip_id(document))

    async def toggle_strategy_status(self, strategy_id: str, is_active: bool) -> None:
        await self._ensure_seeded()
        document = await self.collection.find_one({})
        if not document:
            return
        strategies = document.get("strategies", [])
        updated = False
        for strategy in strategies:
            if strategy.get("id") == strategy_id:
                strategy["status"] = "active" if is_active else "inactive"
                updated = True
        if updated:
            await self.collection.update_one(
                {"_id": document["_id"]},
                {
                    "$set": {
                        "strategies": strategies,
                        "updated_at": datetime.datetime.utcnow(),
                    }
                },
            )

    async def _ensure_seeded(self) -> None:
        if await self.collection.count_documents({}) > 0:
            return
        await self.collection.insert_one(
            {**self.DEFAULT_OVERVIEW, "updated_at": datetime.datetime.utcnow()}
        )
