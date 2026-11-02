from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class LogEntry:
    at: str
    level: str
    logger: str
    message: str


class RecentLogs(logging.Handler):
    """Keeps the last warnings and errors in memory for the admin page.

    The host keeps the full log; this is the "what went wrong lately" view
    that needs no log service.
    """

    def __init__(self, size: int = 100):
        super().__init__(level=logging.WARNING)
        self._entries: deque[LogEntry] = deque(maxlen=size)

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if record.exc_info:
            message += f" — {record.exc_info[1]!r}"
        at = datetime.fromtimestamp(record.created, UTC).isoformat(timespec="seconds")
        self._entries.append(LogEntry(at, record.levelname, record.name, message[:500]))

    def entries(self) -> list[LogEntry]:
        return list(reversed(self._entries))
