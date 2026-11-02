"""Reads how much memory and CPU this process is using against its limits.

On Linux hosts (Render) the limits come from the container's cgroup. Where
none can be read — a laptop — the configured limits are used, and with none
configured the percentages are unknown (``None``).
"""

from __future__ import annotations

import os
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path

CGROUP = Path("/sys/fs/cgroup")


@dataclass(frozen=True)
class Sample:
    at: float              # monotonic seconds
    memory_used: int       # bytes
    memory_limit: int | None
    cpu_seconds: float     # CPU time used so far
    cpu_cores: float | None

    @property
    def memory_percent(self) -> float | None:
        return round(100 * self.memory_used / self.memory_limit, 1) if self.memory_limit else None


def _read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


class ResourceProbe:
    def __init__(self, memory_limit_mb: int = 0, cpu_cores: float = 0):
        self._memory_limit = memory_limit_mb * 1024 * 1024 or None
        self._cpu_cores = cpu_cores or None

    def sample(self) -> Sample:
        return Sample(
            at=time.monotonic(),
            memory_used=self._memory_used(),
            memory_limit=self._memory_limit or self._cgroup_memory_limit(),
            cpu_seconds=self._cpu_seconds(),
            cpu_cores=self._cpu_cores or self._cgroup_cpu_cores(),
        )

    @staticmethod
    def cpu_percent(earlier: Sample, later: Sample) -> float | None:
        elapsed = later.at - earlier.at
        if elapsed <= 0 or not later.cpu_cores:
            return None
        return round(100 * (later.cpu_seconds - earlier.cpu_seconds) / (elapsed * later.cpu_cores), 1)

    # --- memory ---------------------------------------------------------

    @staticmethod
    def _memory_used() -> int:
        for path in (CGROUP / "memory.current", CGROUP / "memory/memory.usage_in_bytes"):
            if (value := _read(path)) and value.isdigit():
                return int(value)
        status = _read(Path("/proc/self/status")) or ""
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak if sys.platform == "darwin" else peak * 1024  # macOS reports bytes, Linux kB

    @staticmethod
    def _cgroup_memory_limit() -> int | None:
        for path in (CGROUP / "memory.max", CGROUP / "memory/memory.limit_in_bytes"):
            value = _read(path)
            if value and value.isdigit() and int(value) < 1 << 60:  # v1 reports "unlimited" as a huge number
                return int(value)
        return None

    # --- cpu ------------------------------------------------------------

    @staticmethod
    def _cpu_seconds() -> float:
        stat = _read(CGROUP / "cpu.stat") or ""
        for line in stat.splitlines():
            if line.startswith("usage_usec"):
                return int(line.split()[1]) / 1_000_000
        if (value := _read(CGROUP / "cpuacct/cpuacct.usage")) and value.isdigit():
            return int(value) / 1_000_000_000
        return time.process_time()

    @staticmethod
    def _cgroup_cpu_cores() -> float | None:
        if value := _read(CGROUP / "cpu.max"):
            quota, _, period = value.partition(" ")
            if quota != "max" and period:
                return int(quota) / int(period)
        quota, period = _read(CGROUP / "cpu/cpu.cfs_quota_us"), _read(CGROUP / "cpu/cpu.cfs_period_us")
        if quota and period and quota.lstrip("-").isdigit() and int(quota) > 0:
            return int(quota) / int(period)
        return float(os.cpu_count() or 1)
