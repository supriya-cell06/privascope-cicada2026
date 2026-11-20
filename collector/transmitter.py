"""Simulated Tier 1 -> Tier 2 Transmitter with Outage Buffering & Deduplication."""
import time
from typing import Any, Dict

from collector.buffer import LocalBuffer
from database.db import DatabaseManager
from utils.timestamps import utc_now_iso


class SaaSTransmitter:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.buffer = LocalBuffer(db)

    def is_saas_online(self) -> bool:
        return self.db.get_state("saas_online", "true").lower() == "true"

    def set_saas_online(self, online: bool):
        self.db.set_state("saas_online", "true" if online else "false")

    def _ingest_to_saas(self, payload: Dict[str, Any]) -> bool:
        t0 = time.perf_counter()
        record = {
            "event_id": payload["event_id"],
            "tenant_id": payload["tenant_id"],
            "source_id": payload["source_id"],
            "timestamp": payload["timestamp"],
            "source_timezone": payload.get("source_timezone", "UTC"),
            "event_category": payload.get("event_category", "infrastructure"),
            "event_type": payload.get("event_type", "metric_sample"),
            "cpu_pct": payload.get("cpu_pct"),
            "memory_pct": payload.get("memory_pct"),
            "disk_pct": payload.get("disk_pct"),
            "network_mbps": payload.get("network_mbps"),
            "inbound_mbps": payload.get("inbound_mbps"),
            "outbound_mbps": payload.get("outbound_mbps"),
            "latency_ms": payload.get("latency_ms"),
            "packet_loss_pct": payload.get("packet_loss_pct"),
            "response_time_ms": payload.get("response_time_ms"),
            "error_rate_pct": payload.get("error_rate_pct"),
            "failed_attempts": int(payload.get("failed_attempts") or 0),
            "severity": payload.get("severity", "INFO"),
            "health_state": payload.get("health_state", "EXCELLENT"),
            "anomaly_score": float(payload.get("anomaly_score") or 0.0),
            "sanitized_summary": payload.get("sanitized_summary", ""),
            "ingested_at": utc_now_iso(),
            "processing_latency_ms": round((time.perf_counter() - t0) * 1000.0 + 18.5, 2),
        }
        return self.db.insert_telemetry(record)

    def transmit(self, sanitized_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_saas_online():
            queued = self.buffer.enqueue(sanitized_payload)
            return {
                "status": "BUFFERED_LOCAL_OUTAGE",
                "delivered": False,
                "buffered": queued,
                "duplicate": False,
            }

        inserted = self._ingest_to_saas(sanitized_payload)
        return {
            "status": "TRANSMITTED" if inserted else "DUPLICATE_DROPPED",
            "delivered": inserted,
            "buffered": False,
            "duplicate": not inserted,
        }

    def flush_buffer(self, tenant_id: str = None) -> Dict[str, int]:
        if not self.is_saas_online():
            return {"delivered": 0, "duplicates_prevented": 0, "remaining": len(self.buffer.get_pending(tenant_id))}

        pending = self.buffer.get_pending(tenant_id)
        delivered = 0
        duplicates = 0
        for item in pending:
            inserted = self._ingest_to_saas(item["payload"])
            self.buffer.mark_delivered(item["event_id"])
            if inserted:
                delivered += 1
            else:
                duplicates += 1

        return {
            "delivered": delivered,
            "duplicates_prevented": duplicates,
            "remaining": len(self.buffer.get_pending(tenant_id)),
        }
