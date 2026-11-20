"""Automated tests for Local Privacy Collector pipeline."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.local_collector import LocalPrivacyCollector
from database.db import DatabaseManager


def test_collector_processes_and_audits():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(str(Path(tmp) / "test.db"))
        col = LocalPrivacyCollector(db)
        res = col.process_raw_telemetry({
            "tenant_id": "Tenant Alpha",
            "source_id": "APP-01",
            "cpu_pct": 42.5,
            "memory_pct": 51.0,
            "PASSWORD": "super-secret-password",
        })
        assert res["transmission"]["status"] == "TRANSMITTED"
        assert "PASSWORD" not in res["sanitized_payload"]
        audits = db.get_privacy_audits("Tenant Alpha")
        assert len(audits) == 1
        assert "PASSWORD" in audits[0]["rejected_fields"]
