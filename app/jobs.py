from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from uuid import uuid4

from app.metrics import inc


@dataclass
class JobState:
    id: str
    kind: str
    status: str
    created_at: str
    updated_at: str
    result: dict | None = None
    error: str | None = None


executor = ThreadPoolExecutor(max_workers=4)
jobs: dict[str, JobState] = {}
lock = Lock()


def enqueue(kind: str, fn, *args, **kwargs) -> str:
    job_id = str(uuid4())
    inc("queue_jobs_total")
    now = datetime.utcnow().isoformat()
    state = JobState(id=job_id, kind=kind, status="queued", created_at=now, updated_at=now)
    with lock:
        jobs[job_id] = state

    def runner():
        with lock:
            state.status = "running"
            state.updated_at = datetime.utcnow().isoformat()
        try:
            result = fn(*args, **kwargs)
            with lock:
                state.status = "completed"
                state.result = result
                state.updated_at = datetime.utcnow().isoformat()
        except Exception as exc:
            with lock:
                state.status = "failed"
                state.error = str(exc)
                inc("queue_jobs_failed")
                state.updated_at = datetime.utcnow().isoformat()

    executor.submit(runner)
    return job_id


def get_job(job_id: str) -> JobState | None:
    with lock:
        return jobs.get(job_id)
