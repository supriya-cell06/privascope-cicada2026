"""Security event monitoring and investigation guidance."""
from typing import Any, Dict, List

from database.db import DatabaseManager


def get_security_events(db: DatabaseManager, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    return db.get_telemetry(tenant_id=tenant_id, category="security", limit=limit)


def suggested_investigation_steps(event_type: str) -> List[str]:
    et = (event_type or "").lower()
    if "authentication" in et or "brute" in et:
        return [
            "Verify whether the target account is an administrative or service account.",
            "Inspect local Tier 1 raw logs (on-premise only) to identify source IP and user agent.",
            "Check if MFA or account lockout policies were triggered.",
            "Consider temporary source restriction via human-approved Autonomous Operations.",
        ]
    if "unauthorized" in et:
        return [
            "Audit IAM / RBAC role bindings for the affected resource.",
            "Review recent token issuance and privilege escalation logs locally.",
            "Validate whether the access attempt originated from an approved maintenance window.",
        ]
    return [
        "Correlate the security alert with concurrent infrastructure and network anomalies.",
        "Inspect local privacy-protected audit trails for additional context.",
        "Escalate to SOC analyst if repeated occurrences persist.",
    ]
