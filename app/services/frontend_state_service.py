import datetime
from typing import Dict, List, Optional

from app.db import db_manager
from app.models.account import AccountProfile, AccountProfileUpdate, PasswordChangeRequest
from app.models.limitup import LimitUpOverview
from app.models.market import MarketDataResponse
from app.models.portfolio import PortfolioOverview
from app.models.settings import SettingsData
from app.models.subscription import StrategySubscriptionState
from app.models.user import User
from app.services.user_service import UserService


def _now_iso() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


class BaseCollectionService:
    def __init__(self, collection_name: str) -> None:
        self.collection = db_manager.get_mongodb_collection(collection_name)

    @staticmethod
    def _strip_id(document: Dict) -> Dict:
        data = dict(document or {})
        data.pop("_id", None)
        return data


class SettingsService(BaseCollectionService):
    DEFAULT_SETTINGS = SettingsData(
        emailConfigs=[
            {"id": "1", "email": "admin@example.com", "remark": "管理员邮箱", "enabled": True},
            {"id": "2", "email": "trader@example.com", "remark": "交易员邮箱", "enabled": True},
        ],
        notificationTemplates=[
            {
                "id": "1",
                "name": "通知模板",
                "subject": "投资组合调仓通知 - {{date}}",
                "content": "策略名称：{{strategyName}}\\n委托时间：{{orderTime}}"
                "\\n{{#orders}}{{stock}}|{{quantity}}|{{orderType}}|{{price}}|{{action}}|{{position}}\\n{{/orders}}",
                "enabled": True,
            }
        ],
    )

    def __init__(self) -> None:
        super().__init__("settings_data")

    async def get_settings(self, username: str) -> SettingsData:
        doc = await self.collection.find_one({"username": username})
        if not doc:
            await self.collection.update_one(
                {"username": username},
                {
                    "$setOnInsert": {
                        "username": username,
                        "data": self.DEFAULT_SETTINGS.dict(),
                        "updated_at": datetime.datetime.utcnow(),
                    }
                },
                upsert=True,
            )
            doc = await self.collection.find_one({"username": username})
        payload = (doc or {}).get("data") or self.DEFAULT_SETTINGS.dict()
        return SettingsData.parse_obj(payload)

    async def save_settings(self, username: str, data: SettingsData) -> None:
        await self.collection.update_one(
            {"username": username},
            {
                "$set": {
                    "data": data.dict(),
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )


class MarketDataService(BaseCollectionService):
    DEFAULT_DATA: Dict[str, Dict] = {
        "shanghaiIndex": {
            "current": 3700.25,
            "change": 1.25,
            "history": [3680.5, 3695.2, 3710.8, 3698.45, 3700.25],
        },
        "nasdaqIndex": {
            "current": 16543.67,
            "change": -0.85,
            "history": [16680.3, 16620.15, 16580.9, 16560.25, 16543.67],
        },
        "goldIndex": {
            "current": 2345.89,
            "change": 2.15,
            "history": [2295.6, 2310.25, 2325.8, 2335.45, 2345.89],
        },
        "zhongzheng2000Index": {
            "current": 1245.67,
            "change": 0.75,
            "history": [1235.2, 1240.8, 1242.5, 1243.9, 1245.67],
        },
    }

    def __init__(self) -> None:
        super().__init__("market_data")

    async def _ensure_seeded(self) -> None:
        count = await self.collection.count_documents({})
        if count > 0:
            return
        for symbol, data in self.DEFAULT_DATA.items():
            await self.collection.insert_one(
                {
                    "symbol": symbol,
                    "current": data["current"],
                    "change": data["change"],
                    "history": data["history"],
                    "updated_at": datetime.datetime.utcnow(),
                }
            )

    async def get_market_data(
        self, symbols: Optional[List[str]], history_days: int
    ) -> MarketDataResponse:
        indices_col = db_manager.get_mongodb_collection("market_indices")
        latest = await indices_col.find_one({"_id": "latest_indices"})
        
        result: Dict[str, Dict] = {}
        if latest:
            # Drop the _id field
            source_data = {k: v for k, v in latest.items() if k != "_id"}
            
            for symbol, data in source_data.items():
                if symbols and symbol not in symbols:
                    continue
                history = list(data.get("history", []))
                history_slice = history[-history_days:] if history_days else history
                result[symbol] = {
                    "current": float(data.get("current", 0)),
                    "change": float(data.get("change", 0)),
                    "history": history_slice,
                }

        # If specific symbols requested but missing, fill from defaults.
        if symbols:
            for symbol in symbols:
                if symbol not in result and symbol in self.DEFAULT_DATA:
                    default = self.DEFAULT_DATA[symbol]
                    result[symbol] = {
                        "current": default["current"],
                        "change": default["change"],
                        "history": default["history"][-history_days:],
                    }

        return MarketDataResponse.parse_obj(result or self.DEFAULT_DATA)


class LimitUpService(BaseCollectionService):
    DEFAULT_OVERVIEW = {
        "date": "2025-08-28",
        "sectors": [
            {"name": "芯片", "count": 27, "value": 21441},
            {"name": "算力", "count": 29, "value": 8221},
            {"name": "人工智能", "count": 31, "value": 7592},
            {"name": "通信", "count": 9, "value": 4830},
            {"name": "证券", "count": 2, "value": 4187},
        ],
        "ladders": [
            {
                "level": 6,
                "count": 1,
                "stocks": [
                    {
                        "name": "科森科技",
                        "code": "603626",
                        "time": "09:43",
                        "price": 10.02,
                        "changePercent": 28.44,
                        "volume1": 84.67,
                        "volume2": 84.67,
                        "ratio1": 0.43,
                        "ratio2": 1.9,
                        "sectors": ["机器人工业"],
                        "marketCap": 45.6,
                        "pe": 25.3,
                        "pb": 2.1,
                    }
                ],
            },
            {
                "level": 3,
                "count": 2,
                "stocks": [
                    {
                        "name": "科银科技",
                        "code": "002177",
                        "time": "09:33",
                        "price": 10.01,
                        "changePercent": 23.12,
                        "volume1": 76.12,
                        "volume2": 67.49,
                        "ratio1": 1.11,
                        "ratio2": 4.15,
                        "sectors": ["通信", "证券"],
                        "marketCap": 56.2,
                        "pe": 31.5,
                        "pb": 2.8,
                    },
                    {
                        "name": "成飞集成",
                        "code": "002190",
                        "time": "09:32",
                        "price": 10.01,
                        "changePercent": 45.52,
                        "volume1": 175.02,
                        "volume2": 175.02,
                        "ratio1": 1.32,
                        "ratio2": 6.01,
                        "sectors": ["军工"],
                        "marketCap": 67.3,
                        "pe": 28.9,
                        "pb": 2.4,
                    },
                ],
            },
            {
                "level": 0,
                "count": 2,
                "stocks": [
                    {
                        "name": "模拟股票1",
                        "code": "000001",
                        "time": "14:30",
                        "price": 9.85,
                        "changePercent": -1.5,
                        "volume1": 45.23,
                        "volume2": 45.23,
                        "ratio1": 0.85,
                        "ratio2": 2.1,
                        "sectors": ["芯片"],
                        "marketCap": 52.1,
                        "pe": 29.3,
                        "pb": 2.3,
                    },
                    {
                        "name": "模拟股票2",
                        "code": "000002",
                        "time": "14:25",
                        "price": 8.92,
                        "changePercent": -2.1,
                        "volume1": 32.15,
                        "volume2": 32.15,
                        "ratio1": 0.72,
                        "ratio2": 1.8,
                        "sectors": ["人工智能"],
                        "marketCap": 41.8,
                        "pe": 23.6,
                        "pb": 1.9,
                    },
                ],
            },
        ],
    }

    def __init__(self) -> None:
        super().__init__("limitup_overview")

    async def _ensure_seeded(self) -> None:
        if await self.collection.count_documents({}) > 0:
            return
        await self.collection.insert_one(
            {**self.DEFAULT_OVERVIEW, "updated_at": datetime.datetime.utcnow()}
        )

    async def get_overview(self, date: Optional[str]) -> LimitUpOverview:
        target_date = date or _now_iso()
        pool_col = db_manager.get_mongodb_collection("limit_up_pool")
        
        # If no date specified, try to find the latest date available in the pool
        if not date:
            latest_doc = await pool_col.find_one({}, sort=[("date", -1)])
            if latest_doc:
                target_date = latest_doc["date"]

        cursor = pool_col.find({"date": target_date})
        stocks = await cursor.to_list(length=None)
        
        if not stocks:
            # Fallback to default mock if db is completely empty
            await self._ensure_seeded()
            doc = await self.collection.find_one({}) or self.DEFAULT_OVERVIEW
            return LimitUpOverview.parse_obj(self._strip_id(doc))
            
        # Group into ladders
        ladders_map = {}
        sectors_map = {}
        for s in stocks:
            days = s.get("limitUpDays", 1)
            if days not in ladders_map:
                ladders_map[days] = []
            
            stock_item = {
                "name": s.get("name", ""),
                "code": s.get("code", ""),
                "time": s.get("firstLimitUpTime", "")[:5] if s.get("firstLimitUpTime") else "",
                "price": s.get("price", 0),
                "changePercent": s.get("changePercent", 0),
                "volume1": round(s.get("limitUpFund", 0) / 10000, 2) if s.get("limitUpFund") else 0,
                "volume2": 0,
                "ratio1": 0,
                "ratio2": 0,
                "sectors": [s.get("industry")] if s.get("industry") else [],
                "marketCap": round(s.get("marketCap", 0) / 100000000, 2) if s.get("marketCap") else 0,
                "pe": 0,
                "pb": 0,
            }
            ladders_map[days].append(stock_item)
            
            ind = s.get("industry", "未知")
            if ind:
                if ind not in sectors_map:
                    sectors_map[ind] = {"count": 0, "value": 0}
                sectors_map[ind]["count"] += 1
                sectors_map[ind]["value"] += (s.get("amount", 0) / 10000)

        ladders = []
        for level in sorted(ladders_map.keys(), reverse=True):
            ladders.append({
                "level": level,
                "count": len(ladders_map[level]),
                "stocks": ladders_map[level]
            })
            
        sectors = []
        for name, data in sectors_map.items():
            sectors.append({
                "name": name,
                "count": data["count"],
                "value": int(data["value"])
            })
        sectors = sorted(sectors, key=lambda x: x["count"], reverse=True)[:10]
        
        return LimitUpOverview.parse_obj({
            "date": target_date,
            "sectors": sectors,
            "ladders": ladders
        })


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
                    },
                    {
                        "key": "2",
                        "stock": "招商银行",
                        "code": "600036",
                        "currentWeight": 8.5,
                        "targetWeight": 8.5,
                        "action": "hold",
                        "price": 35.2,
                        "quantity": 0,
                        "status": "completed",
                        "createdAt": "2024-01-13",
                        "marketValue": 0,
                    },
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

    async def _ensure_seeded(self) -> None:
        if await self.collection.count_documents({}) > 0:
            return
        await self.collection.insert_one(
            {**self.DEFAULT_OVERVIEW, "updated_at": datetime.datetime.utcnow()}
        )

    async def get_overview(self) -> PortfolioOverview:
        await self._ensure_seeded()
        doc = await self.collection.find_one({}) or self.DEFAULT_OVERVIEW
        return PortfolioOverview.parse_obj(self._strip_id(doc))

    async def toggle_strategy_status(self, strategy_id: str, is_active: bool) -> None:
        await self._ensure_seeded()
        doc = await self.collection.find_one({})
        if not doc:
            return
        
        updated = False
        strategies = doc.get("strategies", [])
        for strat in strategies:
            if strat.get("id") == strategy_id:
                strat["status"] = "active" if is_active else "inactive"
                updated = True
                
        if updated:
            await self.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"strategies": strategies, "updated_at": datetime.datetime.utcnow()}}
            )


class StrategySubscriptionService(BaseCollectionService):
    DEFAULT_STATE = {
        "strategies": [
            {
                "id": "alpha-trend",
                "name": "Alpha趋势跟踪",
                "summary": "捕捉高胜率趋势行情，聚焦放量突破与动量修复的组合交易信号",
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

    def __init__(self) -> None:
        super().__init__("strategy_subscriptions")

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

    async def get_state(self, username: str) -> StrategySubscriptionState:
        await self._ensure_seeded(username)
        doc = await self.collection.find_one({"username": username})
        state = (doc or {}).get("state") or self.DEFAULT_STATE
        
        # Cross reference with PortfolioService
        portfolio_service = PortfolioService()
        portfolio_overview = await portfolio_service.get_overview()
        active_strategies = [s for s in portfolio_overview.strategies if s.status == "active"]
        
        # Build merged strategy list
        existing_subs = {s["id"]: s for s in state.get("strategies", [])}
        merged_strategies = []
        for active in active_strategies:
            if active.id in existing_subs:
                merged_strategies.append(existing_subs[active.id])
            else:
                # Default map from Portfolio
                merged_strategies.append({
                    "id": active.id,
                    "name": active.name,
                    "summary": active.description or "基于基本面与量化的综合策略",
                    "riskLevel": "中",
                    "signalFrequency": "日内/收盘",
                    "lastSignal": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                    "performance": 0.0,
                    "subscribed": False,
                    "channels": ["email"],
                    "tags": ["系统推荐"],
                    "subscribers": 1,
                })
        
        state["strategies"] = merged_strategies
        return StrategySubscriptionState.parse_obj(state)

    async def set_subscribed(
        self, username: str, strategy_id: str, subscribed: bool, channels: Optional[List[str]]
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


class AccountService:
    def __init__(self, user_service: Optional[UserService] = None) -> None:
        self.user_service = user_service or UserService()
        self.settings_service = SettingsService()

    async def get_profile(self, user: User) -> AccountProfile:
        return AccountProfile(
            username=user.username,
            email=user.email,
            role="admin" if user.is_superuser else "user",
            display_name=user.display_name or user.username,
            avatar_url=user.avatar_url,
        )

    async def update_profile(self, user: User, payload: AccountProfileUpdate) -> AccountProfile:
        await self.user_service.update_user(
            user.id,
            UserUpdate(
                username=payload.username or user.username,
                display_name=payload.display_name or payload.username,
                avatar_url=payload.avatar_url or user.avatar_url,
                email=payload.email or user.email,
            ),
        )
        refreshed = await self.user_service.get_user_by_id(user.id) or user
        return await self.get_profile(refreshed)

    async def change_password(self, user: User, payload: PasswordChangeRequest) -> None:
        authed = await self.user_service.authenticate_user(user.username, payload.currentPassword)
        if not authed:
            raise ValueError("当前密码错误")
        await self.user_service.update_user(
            user.id,
            UserUpdate(password=payload.newPassword),
        )


# Late import to avoid circular reference within AccountService
from app.models.user import UserUpdate  # noqa: E402  pylint: disable=C0411,C0413
