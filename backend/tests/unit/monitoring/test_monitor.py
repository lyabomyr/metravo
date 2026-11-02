import logging

from app.services.monitoring.log_buffer import RecentLogs
from app.services.monitoring.monitor import HealthMonitor, Thresholds
from app.services.monitoring.probe import ResourceProbe, Sample
from app.services.scanning.models import ScanReport

MB = 1024 * 1024


class FakeProbe(ResourceProbe):
    def __init__(self):
        super().__init__()
        self.memory, self.cpu, self.at = 100 * MB, 0.0, 0.0

    def sample(self):
        self.at += 60
        return Sample(at=self.at, memory_used=self.memory, memory_limit=512 * MB, cpu_seconds=self.cpu, cpu_cores=0.1)


class FakeAlerter:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)


def make(window=2):
    probe, alerter = FakeProbe(), FakeAlerter()
    return HealthMonitor(probe, alerter, Thresholds(cpu_window=window)), probe, alerter


def test_memory_over_80_percent_alerts_once_and_says_when_it_is_over():
    monitor, probe, alerter = make()
    probe.memory = 420 * MB
    monitor.check()
    monitor.check()
    probe.memory = 200 * MB
    monitor.check()
    assert alerter.sent == ["memory at 82.0% of 512 MB", "✅ resolved: memory at 82.0% of 512 MB"]


def test_cpu_alert_needs_a_sustained_load():
    monitor, probe, alerter = make(window=2)
    for _ in range(3):
        probe.cpu += 5.4  # 5.4 s of CPU per minute on 0.1 core = 90 %
        monitor.check()
    assert monitor.status.cpu_percent == 90.0
    assert any("CPU at 90.0%" in text for text in alerter.sent)


def test_a_portal_failing_three_scans_in_a_row_alerts():
    monitor, _, alerter = make()
    for _ in range(3):
        monitor.record_scan(ScanReport(searches_scanned=1, errors=["olx: 403"]))
        monitor.check()
    assert alerter.sent == ["olx failed 3 scans in a row"]
    monitor.record_scan(ScanReport(searches_scanned=1))
    monitor.check()
    assert alerter.sent[-1] == "✅ resolved: olx failed 3 scans in a row"


def test_a_crashed_scan_alerts():
    monitor, _, alerter = make()
    monitor.record_scan_failure(RuntimeError("db down"))
    monitor.check()
    assert "the scan crashed" in alerter.sent[0]


def test_cpu_percent_from_two_samples():
    earlier = Sample(at=0, memory_used=0, memory_limit=None, cpu_seconds=10, cpu_cores=0.5)
    later = Sample(at=60, memory_used=0, memory_limit=None, cpu_seconds=25, cpu_cores=0.5)
    assert ResourceProbe.cpu_percent(earlier, later) == 50.0


def test_real_probe_reads_something_on_this_machine():
    sample = ResourceProbe(memory_limit_mb=512).sample()
    assert sample.memory_used > 0 and sample.memory_percent is not None


def test_recent_logs_keep_warnings_newest_first():
    buffer = RecentLogs(size=2)
    log = logging.getLogger("test.monitor")
    log.addHandler(buffer)
    log.info("ignored")
    log.warning("one")
    log.error("two")
    log.error("three")
    log.removeHandler(buffer)
    assert [entry.message for entry in buffer.entries()] == ["three", "two"]


def test_admin_alerts_reach_the_admin_telegram_chat(container, sign_in, telegram):
    from tests.unit.conftest import ADMIN_EMAIL

    admin = sign_in(ADMIN_EMAIL)
    link = container.telegram_links.create_link(admin)
    container.telegram_links.consume(link.token, "777", "admin")
    container.monitor._alerter.send("memory at 85%")
    assert telegram.outbox[-1].chat_id == "777" and "memory at 85%" in telegram.outbox[-1].text


def test_system_endpoint_is_for_admins(client):
    from tests.unit.conftest import ADMIN_EMAIL

    def headers(email):
        token = client.post("/api/auth/session", json={"provider": "dev", "credential": email}).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    assert client.get("/api/admin/system", headers=headers("user@x.pl")).status_code == 403
    body = client.get("/api/admin/system", headers=headers(ADMIN_EMAIL)).json()
    assert body["memory_used_mb"] > 0 and "recent_logs" in body
