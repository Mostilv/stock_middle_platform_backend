from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from .models import MailLog

_MAIL_LOGS: List[MailLog] = []
_MAIL_ID = 1


async def log_mail(session, subject: str, recipients: Iterable[str], ok: bool, error: str | None) -> MailLog:
    global _MAIL_ID
    entry = MailLog(
        id=_MAIL_ID,
        sent_at=datetime.utcnow(),
        subject=subject,
        recipients=list(recipients),
        ok=ok,
        error=error,
    )
    _MAIL_ID += 1
    _MAIL_LOGS.append(entry)
    return entry


__all__ = ["log_mail"]
