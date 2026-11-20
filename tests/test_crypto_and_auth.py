"""Automated tests for HMAC-SHA256 Signing, Hash-Chained Audit Ledger, Differential Privacy & Multi-Auth RBAC."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.crypto_privacy import (
    apply_differential_privacy,
    sign_payload,
    verify_audit_chain,
    verify_payload_signature,
)
from collector.local_collector import LocalPrivacyCollector
from database.db import DatabaseManager
from utils.auth import (
    USERS_DB,
    authenticate_api_key,
    authenticate_password_mfa,
    generate_totp,
    has_permission,
)


def test_hmac_and_hash_chain_tamper_detection():
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(str(Path(tmp) / "crypto.db"))
        col = LocalPrivacyCollector(db)
        r1 = col.process_raw_telemetry({"tenant_id": "Tenant Alpha", "source_id": "APP-01", "cpu_pct": 40.0})
        r2 = col.process_raw_telemetry({"tenant_id": "Tenant Alpha", "source_id": "DB-01", "cpu_pct": 55.0})

        assert verify_payload_signature(r1["sanitized_payload"], r1["payload_hmac"]) is True
        assert verify_payload_signature(r1["sanitized_payload"], "bad_signature") is False

        chron = db.get_privacy_audits_chronological("Tenant Alpha")
        ok, _ = verify_audit_chain(chron)
        assert ok is True

        # Tamper with record #1 and confirm chain verification catches it
        chron[0]["sanitized_payload"]["cpu_pct"] = 99.9
        ok_tampered, msg = verify_audit_chain(chron)
        assert ok_tampered is False
        assert "Tampering detected" in msg


def test_differential_privacy_and_multi_auth_rbac():
    noisy = apply_differential_privacy(50.0, epsilon=1.0)
    assert noisy >= 0.0

    # Password + live RFC 6238 TOTP MFA
    otp = generate_totp(USERS_DB["admin"]["totp_secret"])
    admin, _ = authenticate_password_mfa("admin", "Admin@2026", otp)
    assert admin is not None and has_permission(admin, "approve_ops")

    # Wrong OTP fails
    bad, _ = authenticate_password_mfa("admin", "Admin@2026", "000000")
    assert bad is None

    # Enterprise API Key auth & RBAC restriction for auditor
    auditor, _ = authenticate_api_key("pk_live_priv_auditor_2026")
    assert auditor is not None
    assert has_permission(auditor, "view") is True
    assert has_permission(auditor, "approve_ops") is False
