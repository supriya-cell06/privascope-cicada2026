"""Automated tests for Multi-Tenant Data Isolation."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.simulation import TelemetrySimulator
from database.db import DatabaseManager


def test_tenant_isolation():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(str(Path(tmp) / "test.db"))
        sim = TelemetrySimulator(db)
        sim.seed_baseline()
        sim.trigger_security_event("Tenant Alpha")

        alpha_alerts = db.get_alerts("Tenant Alpha")
        beta_alerts = db.get_alerts("Tenant Beta")
        gamma_alerts = db.get_alerts("Tenant Gamma")

        assert len(alpha_alerts) >= 1
        assert len(beta_alerts) == 0
        assert len(gamma_alerts) == 0

        alpha_devices = {d["source_id"] for d in db.get_devices("Tenant Alpha")}
        beta_devices = {d["source_id"] for d in db.get_devices("Tenant Beta")}
        assert alpha_devices.isdisjoint(beta_devices)
