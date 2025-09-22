from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import JobLog

_JOBS: list[JobLog] = []
_JOB_ID = 1


async def log_job_start(session, job_name: str) -> JobLog:
    global _JOB_ID
    entry = JobLog(id=_JOB_ID, job_name=job_name, started_at=datetime.utcnow())
    _JOB_ID += 1
    _JOBS.append(entry)
    return entry


async def log_job_end(session, job: JobLog, ok: bool, error: Optional[str] = None) -> None:
    job.finished_at = datetime.utcnow()
    job.ok = ok
    job.error = error


__all__ = ["log_job_start", "log_job_end"]
