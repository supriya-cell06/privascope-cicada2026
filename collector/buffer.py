"""Persistent SQLite Local Buffer for SaaS Outage Resilience."""
from typing import Any, Dict, List, Optional

from database.db import DatabaseManager


class LocalBuffer:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def enqueue(self, payload: Dict[str, Any]) -> bool:
        event_id = payload["event_id"]
        tenant_id = payload["tenant_id"]
        source_id = payload["source_id"]
        return self.db.buffer_event(event_id, tenant_id, source_id, payload)

    def get_pending(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.db.get_buffered_events(tenant_id=tenant_id, status="PENDING")

    def get_all(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.db.get_buffered_events(tenant_id=tenant_id)

    def mark_delivered(self, event_id: str):
        self.db.mark_buffer_delivered(event_id)
