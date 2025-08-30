from typing import Optional, List
from datetime import datetime
from app.database import mongodb
from app.models.strategy import (
    StrategyInDB, Strategy, StrategyCreate, StrategyUpdate,
    StrategySubscription, StrategySubscriptionCreate, StrategySubscriptionResponse
)
from bson import ObjectId


class StrategyService:
    def __init__(self):
        self.collection = mongodb.db.strategies
        self.subscription_collection = mongodb.db.strategy_subscriptions

    async def create_strategy(self, strategy_create: StrategyCreate, user_id: str) -> Strategy:
        """创建策略"""
        strategy_dict = strategy_create.dict()
        strategy_dict["user_id"] = user_id
        strategy_dict["created_at"] = datetime.utcnow()
        strategy_dict["updated_at"] = datetime.utcnow()
        
        strategy_in_db = StrategyInDB(**strategy_dict)
        result = await self.collection.insert_one(strategy_in_db.dict(by_alias=True))
        
        created_strategy = await self.get_strategy_by_id(str(result.inserted_id))
        return created_strategy

    async def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """根据ID获取策略"""
        strategy_doc = await self.collection.find_one({"_id": ObjectId(strategy_id)})
        if strategy_doc:
            strategy_doc["id"] = str(strategy_doc["_id"])
            return Strategy(**strategy_doc)
        return None

    async def get_strategies_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取用户的策略列表"""
        strategies = []
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        async for strategy_doc in cursor:
            strategy_doc["id"] = str(strategy_doc["_id"])
            strategies.append(Strategy(**strategy_doc))
        return strategies

    async def get_public_strategies(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取公开策略列表"""
        strategies = []
        cursor = self.collection.find({"is_public": True, "is_active": True}).skip(skip).limit(limit)
        async for strategy_doc in cursor:
            strategy_doc["id"] = str(strategy_doc["_id"])
            strategies.append(Strategy(**strategy_doc))
        return strategies

    async def update_strategy(self, strategy_id: str, strategy_update: StrategyUpdate, user_id: str) -> Optional[Strategy]:
        """更新策略"""
        # 检查策略是否存在且属于该用户
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return None
        
        update_data = strategy_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(strategy_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_strategy_by_id(strategy_id)
        return None

    async def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        """删除策略"""
        # 检查策略是否存在且属于该用户
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return False
        
        result = await self.collection.delete_one({"_id": ObjectId(strategy_id)})
        return result.deleted_count > 0

    async def subscribe_strategy(self, subscription_create: StrategySubscriptionCreate, user_id: str) -> StrategySubscriptionResponse:
        """订阅策略"""
        # 检查策略是否存在
        strategy = await self.get_strategy_by_id(subscription_create.strategy_id)
        if not strategy:
            raise ValueError("策略不存在")
        
        # 检查是否已经订阅
        existing_subscription = await self.subscription_collection.find_one({
            "user_id": user_id,
            "strategy_id": subscription_create.strategy_id
        })
        
        if existing_subscription:
            raise ValueError("已经订阅该策略")
        
        # 创建订阅
        subscription_dict = subscription_create.dict()
        subscription_dict["user_id"] = user_id
        subscription_dict["created_at"] = datetime.utcnow()
        
        subscription = StrategySubscription(**subscription_dict)
        result = await self.subscription_collection.insert_one(subscription.dict(by_alias=True))
        
        # 返回订阅信息
        subscription_doc = await self.subscription_collection.find_one({"_id": result.inserted_id})
        subscription_doc["id"] = str(subscription_doc["_id"])
        
        return StrategySubscriptionResponse(
            **subscription_doc,
            strategy=strategy
        )

    async def unsubscribe_strategy(self, strategy_id: str, user_id: str) -> bool:
        """取消订阅策略"""
        result = await self.subscription_collection.delete_one({
            "user_id": user_id,
            "strategy_id": strategy_id
        })
        return result.deleted_count > 0

    async def get_user_subscriptions(self, user_id: str) -> List[StrategySubscriptionResponse]:
        """获取用户的策略订阅列表"""
        subscriptions = []
        cursor = self.subscription_collection.find({"user_id": user_id})
        async for subscription_doc in cursor:
            subscription_doc["id"] = str(subscription_doc["_id"])
            
            # 获取策略信息
            strategy = await self.get_strategy_by_id(subscription_doc["strategy_id"])
            
            subscriptions.append(StrategySubscriptionResponse(
                **subscription_doc,
                strategy=strategy
            ))
        return subscriptions

    async def get_all_strategies(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取所有策略（管理员功能）"""
        strategies = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for strategy_doc in cursor:
            strategy_doc["id"] = str(strategy_doc["_id"])
            strategies.append(Strategy(**strategy_doc))
        return strategies
