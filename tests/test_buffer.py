"""Automated tests for SaaS Outage Local Buffering & Duplicate Prevention."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.local_collector import LocalPrivacyCollector
from database.db import DatabaseManager


def test_outage_buffer_and_deduplication():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(str(Path(tmp) / "test.db"))
        col = LocalPrivacyCollector(db)

        # Simulate SaaS Outage
        col.transmitter.set_saas_online(False)
        res = col.process_raw_telemetry({
            "event_id": "EVT-BUF-100",
            "tenant_id": "Tenant Alpha",
            "source_id": "APP-01",
            "cpu_pct": 55.0,
        })
        assert res["transmission"]["status"] == "BUFFERED_LOCAL_OUTAGE"
        assert len(db.get_telemetry("Tenant Alpha")) == 0
        assert len(col.transmitter.buffer.get_pending("Tenant Alpha")) == 1

        # Restore SaaS Connection & Flush
        col.transmitter.set_saas_online(True)
        flush1 = col.transmitter.flush_buffer("Tenant Alpha")
        assert flush1["delivered"] == 1
        assert flush1["remaining"] == 0
        assert len(db.get_telemetry("Tenant Alpha")) == 1

        # Duplicate event must be dropped
        dup = col.transmitter.transmit(res["sanitized_payload"])
        assert dup["duplicate"] is True
        assert len(db.get_telemetry("Tenant Alpha")) == 1
