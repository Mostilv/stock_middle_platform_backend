from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import IndicatorDef

_DEFS: list[IndicatorDef] = []
_DEF_ID = 1


async def get_by_name(session, name: str) -> Optional[IndicatorDef]:
    for item in _DEFS:
        if item.name == name:
            return item
    return None


async def create_or_update(
    session,
    name: str,
    description: str,
    params_schema: dict,
    impl_ref: str,
) -> IndicatorDef:
    global _DEF_ID
    record = await get_by_name(session, name)
    now = datetime.utcnow()
    if record is None:
        record = IndicatorDef(
            id=_DEF_ID,
            name=name,
            description=description,
            params_schema=params_schema,
            impl_ref=impl_ref,
            created_at=now,
            updated_at=now,
        )
        _DEFS.append(record)
        _DEF_ID += 1
    else:
        record.description = description
        record.params_schema = params_schema
        record.impl_ref = impl_ref
        record.updated_at = now
    return record


async def list_defs(session) -> list[IndicatorDef]:
    return sorted(_DEFS, key=lambda item: item.name)


__all__ = ["create_or_update", "get_by_name", "list_defs"]
