"""Human approval, simulated execution, and rollback workflows."""
from database.db import DatabaseManager


def approve_action(db: DatabaseManager, action_id: str, tenant_id: str, approver: str = "SOC-Lead"):
    db.update_autonomous_action(action_id, tenant_id, approval_status="APPROVED", approved_by=approver)


def reject_action(db: DatabaseManager, action_id: str, tenant_id: str, approver: str = "SOC-Lead"):
    db.update_autonomous_action(
        action_id, tenant_id, approval_status="REJECTED", execution_status="CANCELLED", approved_by=approver
    )


def simulate_execute_action(db: DatabaseManager, action_id: str, tenant_id: str) -> bool:
    actions = [a for a in db.get_autonomous_actions(tenant_id) if a["action_id"] == action_id]
    if not actions or actions[0]["approval_status"] != "APPROVED":
        return False
    db.update_autonomous_action(action_id, tenant_id, execution_status="SIMULATED_SUCCESS")
    return True


def rollback_action(db: DatabaseManager, action_id: str, tenant_id: str):
    db.update_autonomous_action(action_id, tenant_id, execution_status="ROLLED_BACK")
