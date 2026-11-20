"""Automated tests for Tier 1 Privacy Filter & Strict Allow-List."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.privacy_filter import filter_telemetry
from config import OUTBOUND_ALLOW_LIST


def test_secrets_never_enter_outbound_metadata():
    raw = {
        "event_id": "EVT-TEST-001",
        "timestamp": "2026-11-20T14:45:12Z",
        "tenant_id": "Tenant Alpha",
        "source_id": "DB-01",
        "event_category": "security",
        "event_type": "repeated_authentication_failure",
        "failed_attempts": 25,
        "severity": "HIGH",
        "health_state": "POOR",
        "PASSWORD": "Admin@123",
        "api_key": "sk-live-secret-99999",
        "auth_token": "Bearer eyJhbGciOiJIUzI1NiJ9.secret",
        "USERNAME": "admin",
        "IP": "192.168.1.50",
        "unknown_custom_field": "should_be_rejected",
        "sanitized_summary": "Login failure for admin@corp.com from 192.168.1.50 with password=Admin@123",
    }
    res = filter_telemetry(raw)
    payload = res["sanitized_payload"]

    assert "PASSWORD" not in payload
    assert "api_key" not in payload
    assert "auth_token" not in payload
    assert "USERNAME" not in payload
    assert "IP" not in payload
    assert "unknown_custom_field" not in payload

    for k in payload:
        assert k in OUTBOUND_ALLOW_LIST

    assert "Admin@123" not in str(payload)
    assert "sk-live-secret-99999" not in str(payload)
    assert "192.168.1.50" not in str(payload)
    assert "PASSWORD" in res["rejected_fields"]
    assert "unknown_custom_field" in res["rejected_fields"]
    assert "sanitized_summary" in res["redacted_fields"]
