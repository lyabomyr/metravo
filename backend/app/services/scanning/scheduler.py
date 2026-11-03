"""Scans on a timer, inside the API process — no external cron needed."""

from __future__ import annotations

import logging
import threading
import time

import requests

from ..monitoring.monitor import HealthMonitor
from ..system.housekeeping import Housekeeping
from .service import ScanService

log = logging.getLogger(__name__)


class KeepAlive:
    """Calls our own health check now and then, so a free host never idles us to sleep."""

    def __init__(self, url: str, every_seconds: int):
        self.url = url
        self.every_seconds = every_seconds
        self._last = 0.0

    def ping_if_due(self, now: float) -> None:
        if now - self._last < self.every_seconds:
            return
        self._last = now
        try:
            requests.get(self.url, timeout=10)
        except requests.RequestException as error:
            log.warning("keep-alive ping failed: %s", error)


class ScanScheduler:
    """Every tick, scan whatever is due, then check the instance's health.

    Each search decides how often it is due. Runs in one background thread. A
    tick never overlaps the previous one, and an error in one tick is logged
    and does not stop the next.
    """

    def __init__(
        self,
        scanner: ScanService,
        tick_seconds: int,
        keep_alive: KeepAlive | None = None,
        monitor: HealthMonitor | None = None,
        housekeeping: Housekeeping | None = None,
    ):
        self._scanner = scanner
        self._tick_seconds = tick_seconds
        self._keep_alive = keep_alive
        self._monitor = monitor
        self._housekeeping = housekeeping
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def tick(self) -> None:
        if self._keep_alive:
            self._keep_alive.ping_if_due(time.monotonic())
        try:
            report = self._scanner.run()
        except Exception as error:  # noqa: BLE001 — the loop must survive anything one run throws
            log.exception("scheduled scan failed")
            if self._monitor:
                self._monitor.record_scan_failure(error)
        else:
            if report.searches_scanned:
                log.info("scheduled scan: %s", report)
            if self._monitor:
                self._monitor.record_scan(report)
        if self._monitor:
            self._check_health()
        if self._housekeeping:
            self._tidy()

    def _tidy(self) -> None:
        try:
            self._housekeeping.run_if_due()
        except Exception:  # noqa: BLE001 — cleaning up must not stop scanning
            log.exception("housekeeping failed")

    def _check_health(self) -> None:
        try:
            self._monitor.check()
        except Exception:  # noqa: BLE001 — a broken probe must not stop scanning
            log.exception("health check failed")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="scan-scheduler", daemon=True)
        self._thread.start()
        log.info("scan scheduler started, tick every %ss", self._tick_seconds)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(self._tick_seconds)
