from __future__ import annotations

from typing import Any, Dict, Optional

from ..repo.mysql import rebalance_repo


class RebalanceService:
    async def list_plans(self, session: Any, limit: int = 20) -> Dict[str, object]:
        plans = await rebalance_repo.list_plans(session, limit)
        return {
            "items": [
                {
                    "plan_id": plan.plan_id,
                    "date": plan.date.isoformat(),
                    "notes": plan.notes,
                }
                for plan in plans
            ]
        }

    async def get_plan(self, session: Any, plan_id: int) -> Dict[str, object]:
        plan = await rebalance_repo.get_plan(session, plan_id)
        if plan is None:
            raise ValueError("Plan not found")
        return {
            "plan_id": plan.plan_id,
            "date": plan.date.isoformat(),
            "targets": plan.targets,
            "estimation": plan.estimation,
            "notes": plan.notes,
        }

    async def confirm_plan(self, session: Any, plan_id: int, notes: Optional[str]) -> Dict[str, object]:
        plan = await rebalance_repo.confirm_plan(session, plan_id, notes)
        if plan is None:
            raise ValueError("Plan not found")
        return {
            "plan_id": plan.plan_id,
            "date": plan.date.isoformat(),
            "notes": plan.notes,
        }


__all__ = ["RebalanceService"]
