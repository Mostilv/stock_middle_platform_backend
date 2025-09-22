from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import RebalancePlan

_PLANS: List[RebalancePlan] = []
_PLAN_ID = 1


async def create_plan(
    session,
    date: datetime,
    targets: Dict[str, Any],
    estimation: Optional[Dict[str, Any]],
    notes: Optional[str],
) -> RebalancePlan:
    global _PLAN_ID
    plan = RebalancePlan(
        plan_id=_PLAN_ID,
        date=date,
        targets=targets,
        estimation=estimation,
        notes=notes,
        created_at=datetime.utcnow(),
    )
    _PLAN_ID += 1
    _PLANS.append(plan)
    return plan


async def list_plans(session, limit: int = 20) -> List[RebalancePlan]:
    return sorted(_PLANS, key=lambda plan: plan.date, reverse=True)[:limit]


async def get_plan(session, plan_id: int) -> Optional[RebalancePlan]:
    for plan in _PLANS:
        if plan.plan_id == plan_id:
            return plan
    return None


async def confirm_plan(session, plan_id: int, notes: Optional[str] = None) -> Optional[RebalancePlan]:
    plan = await get_plan(session, plan_id)
    if plan is None:
        return None
    if notes is not None:
        plan.notes = notes
    return plan


__all__ = ["create_plan", "list_plans", "get_plan", "confirm_plan"]
