from app.services.scanning.models import ScanReport
from app.services.scanning.scheduler import KeepAlive, ScanScheduler


class CountingScanner:
    def __init__(self, fail: bool = False):
        self.runs = 0
        self.fail = fail

    def run(self):
        self.runs += 1
        if self.fail:
            raise RuntimeError("portal down")
        return ScanReport()


def test_each_tick_runs_a_scan():
    scanner = CountingScanner()
    scheduler = ScanScheduler(scanner, tick_seconds=60)
    scheduler.tick()
    scheduler.tick()
    assert scanner.runs == 2


def test_a_failing_scan_does_not_stop_the_scheduler():
    scanner = CountingScanner(fail=True)
    scheduler = ScanScheduler(scanner, tick_seconds=60)
    scheduler.tick()
    scheduler.tick()
    assert scanner.runs == 2


def test_scheduler_thread_starts_and_stops():
    scanner = CountingScanner()
    scheduler = ScanScheduler(scanner, tick_seconds=3600)
    scheduler.start()
    scheduler.stop()
    assert scanner.runs == 1


def test_keep_alive_pings_at_most_once_per_period(monkeypatch):
    calls = []
    monkeypatch.setattr("app.services.scanning.scheduler.requests.get", lambda url, timeout: calls.append(url))
    keep_alive = KeepAlive("https://api/api/health", every_seconds=600)
    keep_alive.ping_if_due(1000)
    keep_alive.ping_if_due(1300)
    keep_alive.ping_if_due(1600)
    assert calls == ["https://api/api/health", "https://api/api/health"]
