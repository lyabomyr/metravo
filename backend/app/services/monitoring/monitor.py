from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from ..scanning.models import ScanReport
from .alerts import AdminAlerter
from .probe import ResourceProbe, Sample


@dataclass(frozen=True)
class Thresholds:
    memory_percent: float = 80
    cpu_percent: float = 80
    #: CPU is averaged over this many samples (one per scheduler tick) so a short burst is not an alert.
    cpu_window: int = 5
    #: A portal failing this many runs in a row is worth a look.
    source_failures: int = 3


@dataclass
class Status:
    started_at: float = field(default_factory=time.monotonic)
    memory_used: int = 0
    memory_limit: int | None = None
    memory_percent: float | None = None
    cpu_percent: float | None = None
    last_scan: ScanReport | None = None
    last_scan_failed: str | None = None
    failing_sources: dict[str, int] = field(default_factory=dict)
    active_alerts: dict[str, str] = field(default_factory=dict)


class HealthMonitor:
    """Watches memory, CPU and scan results; alerts admins when a problem starts and when it ends."""

    def __init__(self, probe: ResourceProbe, alerter: AdminAlerter, thresholds: Thresholds | None = None):
        self._probe = probe
        self._alerter = alerter
        self._limits = thresholds or Thresholds()
        self._samples: deque[Sample] = deque(maxlen=self._limits.cpu_window + 1)
        self.status = Status()

    def record_scan(self, report: ScanReport) -> None:
        # Most ticks find nothing due; keep the last scan that did something, so the admin page shows it.
        if report.searches_scanned or self.status.last_scan is None:
            self.status.last_scan = report
        self.status.last_scan_failed = None
        failed = {error.split(":", 1)[0] for error in report.errors}
        streaks = self.status.failing_sources
        for source in failed:
            streaks[source] = streaks.get(source, 0) + 1
        for source in list(streaks):
            if source not in failed and report.searches_scanned:
                del streaks[source]

    def record_scan_failure(self, error: Exception) -> None:
        self.status.last_scan_failed = repr(error)[:300]

    def check(self) -> None:
        sample = self._probe.sample()
        self._samples.append(sample)
        status = self.status
        status.memory_used, status.memory_limit, status.memory_percent = sample.memory_used, sample.memory_limit, sample.memory_percent
        status.cpu_percent = self._probe.cpu_percent(self._samples[0], sample) if len(self._samples) > 1 else None

        limits = self._limits
        self._flag("memory", (status.memory_percent or 0) >= limits.memory_percent,
                   f"memory at {status.memory_percent}% of {self._mb(status.memory_limit)} MB")
        cpu_window_full = len(self._samples) > limits.cpu_window
        self._flag("cpu", cpu_window_full and (status.cpu_percent or 0) >= limits.cpu_percent,
                   f"CPU at {status.cpu_percent}% of the limit for {limits.cpu_window} minutes — the instance is too small")
        self._flag("scan", status.last_scan_failed is not None, f"the scan crashed: {status.last_scan_failed}")
        for source, streak in list(status.failing_sources.items()) + [(s, 0) for s in self._alerted_sources()]:
            self._flag(f"source:{source}", streak >= limits.source_failures, f"{source} failed {streak} scans in a row")

    def _alerted_sources(self) -> list[str]:
        return [key.split(":", 1)[1] for key in self.status.active_alerts if key.startswith("source:")
                and key.split(":", 1)[1] not in self.status.failing_sources]

    def _flag(self, key: str, is_bad: bool, text: str) -> None:
        active = self.status.active_alerts
        if is_bad and key not in active:
            active[key] = text
            self._alerter.send(text)
        elif not is_bad and key in active:
            self._alerter.send(f"✅ resolved: {active.pop(key)}")

    @staticmethod
    def _mb(value: int | None) -> int | None:
        return value // (1024 * 1024) if value else None
