from __future__ import annotations

import time
from dataclasses import asdict

from pydantic import BaseModel

from .log_buffer import LogEntry
from .monitor import Status


class SystemOut(BaseModel):
    uptime_seconds: int
    memory_used_mb: float
    memory_limit_mb: float | None
    memory_percent: float | None
    cpu_percent: float | None
    last_scan: dict | None
    last_scan_failed: str | None
    failing_sources: dict[str, int]
    active_alerts: dict[str, str]
    recent_logs: list[dict]

    @classmethod
    def of(cls, status: Status, logs: list[LogEntry]) -> SystemOut:
        mb = 1024 * 1024
        return cls(
            uptime_seconds=int(time.monotonic() - status.started_at),
            memory_used_mb=round(status.memory_used / mb, 1),
            memory_limit_mb=round(status.memory_limit / mb, 1) if status.memory_limit else None,
            memory_percent=status.memory_percent,
            cpu_percent=status.cpu_percent,
            last_scan=asdict(status.last_scan) if status.last_scan else None,
            last_scan_failed=status.last_scan_failed,
            failing_sources=status.failing_sources,
            active_alerts=status.active_alerts,
            recent_logs=[asdict(entry) for entry in logs],
        )
