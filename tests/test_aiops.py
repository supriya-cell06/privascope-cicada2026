"""Automated tests for AIOps Anomaly Detection & Incident Correlation."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiops.anomaly_detection import AnomalyDetector
from data.simulation import TelemetrySimulator
from database.db import DatabaseManager


def test_anomaly_detection_and_correlation():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(str(Path(tmp) / "test.db"))
        sim = TelemetrySimulator(db)
        sim.seed_baseline()

        # Normal baseline should not constantly flag anomalies
        det = AnomalyDetector(db)
        normal_anoms = det.detect_for_tenant("Tenant Alpha")
        assert len(normal_anoms) == 0

        # Multiple related alerts -> anomaly + correlated incident with evidence
        sim.trigger_multiple_related_alerts("Tenant Alpha")
        anoms = db.get_anomalies("Tenant Alpha")
        incidents = db.get_incidents("Tenant Alpha")
        assert len(anoms) >= 1
        assert len(incidents) >= 1
        assert len(incidents[0]["evidence"]) >= 2
        assert "APP-01" in incidents[0]["root_cause_hypothesis"]
