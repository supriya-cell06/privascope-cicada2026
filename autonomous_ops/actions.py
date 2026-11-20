"""Safe, simulated Autonomous Operations proposals (human-in-the-loop)."""
from typing import Any, Dict

from database.db import DatabaseManager
from utils.helpers import generate_id
from utils.timestamps import utc_now_iso


def propose_action(
    db: DatabaseManager,
    tenant_id: str,
    source_id: str,
    proposed_action: str,
    reason: str,
    evidence: str,
    expected_outcome: str,
    risk_level: str = "MEDIUM",
    reversibility: str = "REVERSIBLE (Simulated Rollback Supported)",
    incident_id: str = None,
) -> Dict[str, Any]:
    now = utc_now_iso()
    action = {
        "action_id": generate_id("ACT"),
        "tenant_id": tenant_id,
        "source_id": source_id,
        "incident_id": incident_id,
        "proposed_action": proposed_action,
        "reason": reason,
        "evidence": evidence,
        "expected_outcome": expected_outcome,
        "risk_level": risk_level,
        "reversibility": reversibility,
        "approval_status": "PENDING",
        "execution_status": "NOT_EXECUTED",
        "approved_by": None,
        "created_at": now,
        "updated_at": now,
    }
    db.insert_autonomous_action(action)
    return action
