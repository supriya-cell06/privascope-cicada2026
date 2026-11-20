"""Audit log access for Autonomous Operations."""
from typing import Any, Dict, List
from database.db import DatabaseManager


def get_action_audit_log(db: DatabaseManager, tenant_id: str) -> List[Dict[str, Any]]:
    return db.get_autonomous_actions(tenant_id)
