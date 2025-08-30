from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.deps import get_current_active_user, get_current_superuser
from app.services.strategy_service import StrategyService
from app.models.strategy import (
    Strategy, StrategyCreate, StrategyUpdate, 
    StrategySubscriptionResponse, StrategySubscriptionCreate
)
from app.models.user import User

router = APIRouter(prefix="/strategies", tags=["策略管理"])


@router.post("/", response_model=Strategy)
async def create_strategy(
    strategy_create: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """创建策略"""
    strategy = await strategy_service.create_strategy(strategy_create, current_user.id)
    return strategy


@router.get("/", response_model=List[Strategy])
async def get_my_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """获取我的策略列表"""
    strategies = await strategy_service.get_strategies_by_user(current_user.id, skip=skip, limit=limit)
    return strategies


@router.get("/public", response_model=List[Strategy])
async def get_public_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    strategy_service: StrategyService = Depends()
):
    """获取公开策略列表（无需认证）"""
    strategies = await strategy_service.get_public_strategies(skip=skip, limit=limit)
    return strategies


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends()
):
    """获取策略详情（公开策略无需认证）"""
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    return strategy


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """更新策略"""
    strategy = await strategy_service.update_strategy(strategy_id, strategy_update, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在或无权限"
        )
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """删除策略"""
    success = await strategy_service.delete_strategy(strategy_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在或无权限"
        )
    return {"message": "策略删除成功"}


@router.post("/{strategy_id}/subscribe", response_model=StrategySubscriptionResponse)
async def subscribe_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """订阅策略"""
    try:
        subscription = await strategy_service.subscribe_strategy(
            StrategySubscriptionCreate(strategy_id=strategy_id),
            current_user.id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{strategy_id}/unsubscribe")
async def unsubscribe_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """取消订阅策略"""
    success = await strategy_service.unsubscribe_strategy(strategy_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    return {"message": "取消订阅成功"}


@router.get("/subscriptions/my", response_model=List[StrategySubscriptionResponse])
async def get_my_subscriptions(
    current_user: User = Depends(get_current_active_user),
    strategy_service: StrategyService = Depends()
):
    """获取我的策略订阅列表"""
    subscriptions = await strategy_service.get_user_subscriptions(current_user.id)
    return subscriptions


# 管理员路由
@router.get("/admin/all", response_model=List[Strategy])
async def get_all_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
    strategy_service: StrategyService = Depends()
):
    """获取所有策略（仅管理员）"""
    strategies = await strategy_service.get_all_strategies(skip=skip, limit=limit)
    return strategies
