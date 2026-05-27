from __future__ import annotations

from threading import Lock

_lock = Lock()
_counters = {
    "http_requests_total": 0,
    "http_requests_4xx": 0,
    "http_requests_5xx": 0,
    "queue_jobs_total": 0,
    "queue_jobs_failed": 0,
}


def inc(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + value


def render_metrics() -> str:
    with _lock:
        lines = [f"{k} {v}" for k, v in _counters.items()]
    lines.append("niscore_up 1")
    return "\n".join(lines) + "\n"
