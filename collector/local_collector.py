"""Tier 1 Local Privacy Collector: End-to-End Local Processing, HMAC Signing & Hash-Chained Audit."""
import json
from typing import Any, Dict

from collector.crypto_privacy import (
    apply_differential_privacy,
    compute_chain_hash,
    sign_payload,
)
from collector.metadata_processor import normalize_raw_telemetry
from collector.privacy_filter import filter_telemetry
from collector.transmitter import SaaSTransmitter
from database.db import DatabaseManager
from utils.helpers import generate_id, payload_size_bytes
from utils.timestamps import utc_now_iso


class LocalPrivacyCollector:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.transmitter = SaaSTransmitter(db)

    def process_raw_telemetry(self, raw_telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full Tier 1 pipeline:
        1. Normalize & classify raw telemetry locally.
        2. Filter & redact sensitive fields via strict allow-list.
        3. Optional Differential Privacy (Laplace noise) on numeric metrics.
        4. Sign sanitized payload with HMAC-SHA256 for secure Tier 1 -> Tier 2 transport.
        5. Transmit sanitized metadata (or buffer locally if SaaS is offline).
        6. Append to tamper-evident SHA-256 Hash-Chained Privacy Audit Ledger.
        """
        thresholds = self.db.get_thresholds()
        normalized = normalize_raw_telemetry(raw_telemetry, thresholds=thresholds)
        filtered = filter_telemetry(normalized)
        sanitized_payload = filtered["sanitized_payload"]

        # Optional Differential Privacy mode
        dp_enabled = self.db.get_state("differential_privacy", "false").lower() == "true"
        if dp_enabled:
            for metric_key in ("cpu_pct", "memory_pct", "latency_ms"):
                if sanitized_payload.get(metric_key) is not None:
                    sanitized_payload[metric_key] = apply_differential_privacy(
                        float(sanitized_payload[metric_key]), epsilon=1.0
                    )

        # Cryptographic HMAC-SHA256 signature for secure Tier 1 -> Tier 2 communication
        payload_hmac = sign_payload(sanitized_payload)

        tx_result = self.transmitter.transmit(sanitized_payload)

        tenant_id = sanitized_payload.get("tenant_id", "Tenant Alpha")
        event_id = sanitized_payload.get("event_id", generate_id("EVT"))
        ts = sanitized_payload.get("timestamp", utc_now_iso())

        prev_hash = self.db.get_last_chain_hash(tenant_id)
        chain_hash = compute_chain_hash(prev_hash, sanitized_payload, ts, event_id)

        audit_id = generate_id("AUD")
        audit_record = {
            "audit_id": audit_id,
            "event_id": event_id,
            "tenant_id": tenant_id,
            "source_id": sanitized_payload.get("source_id", "UNKNOWN"),
            "timestamp": ts,
            "raw_telemetry_json": json.dumps(raw_telemetry, default=str),
            "sanitized_payload_json": json.dumps(sanitized_payload, default=str),
            "allowed_fields_json": json.dumps(filtered["allowed_fields"]),
            "rejected_fields_json": json.dumps(filtered["rejected_fields"]),
            "redacted_fields_json": json.dumps(filtered["redacted_fields"]),
            "payload_size_bytes": payload_size_bytes(sanitized_payload),
            "policy_status": filtered["policy_status"] + (" + DP_LAPLACE" if dp_enabled else ""),
            "transmission_status": tx_result["status"],
            "payload_hmac": payload_hmac,
            "prev_hash": prev_hash,
            "chain_hash": chain_hash,
        }
        self.db.insert_privacy_audit(audit_record)

        return {
            "audit_id": audit_id,
            "raw_telemetry": raw_telemetry,
            "sanitized_payload": sanitized_payload,
            "allowed_fields": filtered["allowed_fields"],
            "rejected_fields": filtered["rejected_fields"],
            "redacted_fields": filtered["redacted_fields"],
            "policy_status": audit_record["policy_status"],
            "transmission": tx_result,
            "payload_size_bytes": audit_record["payload_size_bytes"],
            "payload_hmac": payload_hmac,
            "chain_hash": chain_hash,
        }
