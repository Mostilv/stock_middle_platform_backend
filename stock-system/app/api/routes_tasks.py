from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from .deps import (
    get_data_service,
    get_db_session,
    get_indicator_service,
    get_mail_service,
    require_api_key,
)
from ..service.data_refresh_service import DataRefreshService
from ..service.indicator_service import IndicatorService
from ..service.mail_service import MailService

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_api_key)])


@router.post("/refresh-daily", summary="Trigger daily refresh")
async def trigger_refresh(
    payload: Dict[str, Any],
    service: DataRefreshService = Depends(get_data_service),
) -> dict:
    codes = payload.get("codes") or ["600519", "000001"]
    days = int(payload.get("days", 5))
    result = await service.refresh_daily(codes, days)
    return result


@router.post("/compute-indicators", summary="Compute indicators")
async def compute_indicators(
    payload: Dict[str, Any],
    indicator_service: IndicatorService = Depends(get_indicator_service),
) -> dict:
    codes: List[str] = payload.get("codes") or ["600519"]
    indicator_names: List[str] = payload.get("indicators") or ["MA", "RSI"]
    start = payload.get("start")
    end = payload.get("end")
    start_date = date.fromisoformat(start) if start else None
    end_date = date.fromisoformat(end) if end else None
    summary: Dict[str, dict] = {}
    for code in codes:
        for name in indicator_names:
            params = {"window": 5}
            if name.upper() == "RSI":
                params = {"window": 14}
            summary_key = f"{code}-{name}"
            summary[summary_key] = await indicator_service.compute_builtin(
                code,
                name,
                params,
                start=start_date,
                end=end_date,
            )
    return summary


@router.post("/mail/preview", summary="Render daily mail preview")
async def preview_mail(
    mail_service: MailService = Depends(get_mail_service),
    session=Depends(get_db_session),
) -> dict:
    html = await mail_service.render_daily_mail(session)
    return {"html": html}


@router.post("/mail/send-today", summary="Send today mail")
async def send_mail(
    payload: Dict[str, Any],
    mail_service: MailService = Depends(get_mail_service),
    session=Depends(get_db_session),
) -> dict:
    html = await mail_service.render_daily_mail(session)
    recipients = payload.get("recipients") or [mail_service.settings.mail_to]
    await mail_service.send_mail(session, html, recipients)
    return {"sent": True, "recipients": recipients}
