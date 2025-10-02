from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import require_permissions
from app.models.joinquant import JoinQuantWebhookPayload
from app.models.strategy import StrategyPosition, StrategySignal
from app.models.user import User
from app.services.joinquant_service import JoinQuantService
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/integrations/joinquant", tags=["聚宽集成"])


def get_joinquant_service(
    strategy_service: StrategyService = Depends(),
) -> JoinQuantService:
    return JoinQuantService(strategy_service)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def joinquant_webhook(
    request: Request,
    service: JoinQuantService = Depends(get_joinquant_service),
):
    """接收聚宽推送的调仓/持仓信号"""

    raw_body = await request.body()
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not service.verify_signature(signature, timestamp, raw_body):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="签名验证失败")

    try:
        payload_dict = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的JSON载荷")

    try:
        payload = JoinQuantWebhookPayload(**payload_dict)
        result = await service.process_webhook(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"message": "聚宽信号已接收", **result}


@router.get("/strategies/{strategy_id}/signals", response_model=List[StrategySignal])
async def get_strategy_signals(
    strategy_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    side: Optional[str] = Query(None, description="按照买卖方向过滤，例如BUY/SELL"),
    start: Optional[datetime] = Query(None, description="起始时间"),
    end: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(require_permissions(["strategies:read"])),
    service: JoinQuantService = Depends(get_joinquant_service),
    strategy_service: StrategyService = Depends(),
):
    """查询策略的调仓信号（需要具备访问权限）"""

    if not (
        current_user.is_superuser
        or await strategy_service.user_has_access_to_strategy(strategy_id, current_user.id)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该策略")

    signals = await service.list_signals(
        strategy_id,
        skip=skip,
        limit=limit,
        side=side,
        start=start,
        end=end,
    )
    return signals


@router.get("/strategies/{strategy_id}/positions", response_model=List[StrategyPosition])
async def get_strategy_positions(
    strategy_id: str,
    current_user: User = Depends(require_permissions(["strategies:read"])),
    service: JoinQuantService = Depends(get_joinquant_service),
    strategy_service: StrategyService = Depends(),
):
    """查询策略的最新持仓快照"""

    if not (
        current_user.is_superuser
        or await strategy_service.user_has_access_to_strategy(strategy_id, current_user.id)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该策略")

    return await service.get_latest_positions(strategy_id)
