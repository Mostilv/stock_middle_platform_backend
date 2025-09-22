from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Header

from .deps import get_db_session, get_jq_service, require_api_key
from ..service.jq_bridge_service import JQBridgeService

router = APIRouter(prefix="/webhook/jq", tags=["webhook"], dependencies=[Depends(require_api_key)])


@router.post("/signal", summary="Receive JoinQuant webhook")
async def receive_signal(
    payload: Dict[str, Any],
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    service: JQBridgeService = Depends(get_jq_service),
    session=Depends(get_db_session),
) -> dict:
    result = await service.process_webhook(session, payload, x_signature, x_timestamp)
    return result
