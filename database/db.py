"""SQLite database manager with strict tenant filtering and deduplication."""
import sqlite3
import json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from config import DB_PATH, TENANTS, DEFAULT_THRESHOLDS
from database.schema import SCHEMA_SQL
from utils.timestamps import utc_now_iso


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self.init_db()

    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.get_conn() as conn:
            conn.executescript(SCHEMA_SQL)
            now = utc_now_iso()
            for t in TENANTS:
                conn.execute(
                    "INSERT OR IGNORE INTO tenants (tenant_id, name, tier, region_primary, created_at) VALUES (?, ?, ?, ?, ?)",
                    (t, t, "Enterprise", "Bengaluru", now),
                )
            defaults = {
                "saas_online": "true",
                "simulation_running": "false",
                "active_scenario": "Normal Operations",
                "differential_privacy": "false",
                "thresholds": json.dumps(DEFAULT_THRESHOLDS),
            }
            for k, v in defaults.items():
                conn.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES (?, ?)", (k, v))

    def get_state(self, key: str, default: str = "") -> str:
        with self.get_conn() as conn:
            row = conn.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_state(self, key: str, value: str):
        with self.get_conn() as conn:
            conn.execute(
                "INSERT INTO system_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )

    def get_thresholds(self) -> Dict[str, float]:
        raw = self.get_state("thresholds", "")
        if not raw:
            return dict(DEFAULT_THRESHOLDS)
        try:
            data = json.loads(raw)
            merged = dict(DEFAULT_THRESHOLDS)
            merged.update(data)
            return merged
        except Exception:
            return dict(DEFAULT_THRESHOLDS)

    def set_thresholds(self, thresholds: Dict[str, float]):
        self.set_state("thresholds", json.dumps(thresholds))

    def reset_all_data(self):
        tables = [
            "telemetry", "alerts", "incidents", "anomalies",
            "privacy_audit", "local_buffer", "autonomous_actions",
            "devices", "collectors"
        ]
        with self.get_conn() as conn:
            for tbl in tables:
                conn.execute(f"DELETE FROM {tbl}")
            conn.execute("UPDATE system_state SET value = 'true' WHERE key = 'saas_online'")
            conn.execute("UPDATE system_state SET value = 'Normal Operations' WHERE key = 'active_scenario'")

    # ---- Devices ----
    def upsert_device(self, device: Dict[str, Any]):
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO devices (
                    source_id, tenant_id, device_name, device_type, environment, region,
                    source_timezone, collector_id, connectivity_status, health_status, last_seen,
                    cpu_pct, memory_pct, disk_pct, network_mbps, inbound_mbps, outbound_mbps,
                    latency_ms, packet_loss_pct, response_time_ms, error_rate_pct
                ) VALUES (
                    :source_id, :tenant_id, :device_name, :device_type, :environment, :region,
                    :source_timezone, :collector_id, :connectivity_status, :health_status, :last_seen,
                    :cpu_pct, :memory_pct, :disk_pct, :network_mbps, :inbound_mbps, :outbound_mbps,
                    :latency_ms, :packet_loss_pct, :response_time_ms, :error_rate_pct
                )
                ON CONFLICT(source_id) DO UPDATE SET
                    connectivity_status=excluded.connectivity_status,
                    health_status=excluded.health_status,
                    last_seen=excluded.last_seen,
                    cpu_pct=excluded.cpu_pct,
                    memory_pct=excluded.memory_pct,
                    disk_pct=excluded.disk_pct,
                    network_mbps=excluded.network_mbps,
                    inbound_mbps=excluded.inbound_mbps,
                    outbound_mbps=excluded.outbound_mbps,
                    latency_ms=excluded.latency_ms,
                    packet_loss_pct=excluded.packet_loss_pct,
                    response_time_ms=excluded.response_time_ms,
                    error_rate_pct=excluded.error_rate_pct
                """,
                device,
            )

    def get_devices(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM devices WHERE tenant_id = ? ORDER BY source_id",
                (tenant_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- Telemetry (with deduplication via PRIMARY KEY event_id) ----
    def insert_telemetry(self, record: Dict[str, Any]) -> bool:
        with self.get_conn() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO telemetry (
                    event_id, tenant_id, source_id, timestamp, source_timezone,
                    event_category, event_type, cpu_pct, memory_pct, disk_pct,
                    network_mbps, inbound_mbps, outbound_mbps, latency_ms,
                    packet_loss_pct, response_time_ms, error_rate_pct,
                    failed_attempts, severity, health_state, anomaly_score,
                    sanitized_summary, ingested_at, processing_latency_ms
                ) VALUES (
                    :event_id, :tenant_id, :source_id, :timestamp, :source_timezone,
                    :event_category, :event_type, :cpu_pct, :memory_pct, :disk_pct,
                    :network_mbps, :inbound_mbps, :outbound_mbps, :latency_ms,
                    :packet_loss_pct, :response_time_ms, :error_rate_pct,
                    :failed_attempts, :severity, :health_state, :anomaly_score,
                    :sanitized_summary, :ingested_at, :processing_latency_ms
                )
                """,
                record,
            )
            return cur.rowcount > 0

    def get_telemetry(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        source_id: Optional[str] = None,
        limit: int = 300,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM telemetry WHERE tenant_id = ?"
        params: List[Any] = [tenant_id]
        if category:
            query += " AND event_category = ?"
            params.append(category)
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        # Order by event timestamp (event-time-based processing)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self.get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # ---- Collectors ----
    def upsert_collector(self, collector: Dict[str, Any]):
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO collectors (
                    collector_id, tenant_id, source_id, version, status, last_heartbeat,
                    cpu_pct, memory_pct, config_status, connectivity, collection_status, last_transmission
                ) VALUES (
                    :collector_id, :tenant_id, :source_id, :version, :status, :last_heartbeat,
                    :cpu_pct, :memory_pct, :config_status, :connectivity, :collection_status, :last_transmission
                )
                ON CONFLICT(collector_id) DO UPDATE SET
                    status=excluded.status,
                    last_heartbeat=excluded.last_heartbeat,
                    cpu_pct=excluded.cpu_pct,
                    memory_pct=excluded.memory_pct,
                    config_status=excluded.config_status,
                    connectivity=excluded.connectivity,
                    collection_status=excluded.collection_status,
                    last_transmission=excluded.last_transmission
                """,
                collector,
            )

    def get_collectors(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM collectors WHERE tenant_id = ? ORDER BY collector_id",
                (tenant_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- Alerts (with duplicate suppression / grouping) ----
    def upsert_alert(self, alert: Dict[str, Any]):
        with self.get_conn() as conn:
            existing = conn.execute(
                """
                SELECT alert_id, occurrence_count FROM alerts
                WHERE tenant_id = ? AND source_id = ? AND title = ? AND status != 'RESOLVED'
                LIMIT 1
                """,
                (alert["tenant_id"], alert["source_id"], alert["title"]),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE alerts SET occurrence_count = ?, updated_at = ?, severity = ?, description = ?
                    WHERE alert_id = ?
                    """,
                    (
                        existing["occurrence_count"] + 1,
                        alert["updated_at"],
                        alert["severity"],
                        alert["description"],
                        existing["alert_id"],
                    ),
                )
                return existing["alert_id"]
            conn.execute(
                """
                INSERT INTO alerts (
                    alert_id, tenant_id, source_id, event_id, category, title,
                    description, severity, status, assigned_to, occurrence_count,
                    created_at, updated_at, detection_latency_sec
                ) VALUES (
                    :alert_id, :tenant_id, :source_id, :event_id, :category, :title,
                    :description, :severity, :status, :assigned_to, :occurrence_count,
                    :created_at, :updated_at, :detection_latency_sec
                )
                """,
                alert,
            )
            return alert["alert_id"]

    def get_alerts(self, tenant_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        q = "SELECT * FROM alerts WHERE tenant_id = ?"
        params: List[Any] = [tenant_id]
        if status:
            q += " AND status = ?"
            params.append(status)
        q += " ORDER BY updated_at DESC"
        with self.get_conn() as conn:
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def update_alert_status(self, alert_id: str, tenant_id: str, status: str, assigned_to: Optional[str] = None):
        with self.get_conn() as conn:
            if assigned_to is not None:
                conn.execute(
                    "UPDATE alerts SET status = ?, assigned_to = ?, updated_at = ? WHERE alert_id = ? AND tenant_id = ?",
                    (status, assigned_to, utc_now_iso(), alert_id, tenant_id),
                )
            else:
                conn.execute(
                    "UPDATE alerts SET status = ?, updated_at = ? WHERE alert_id = ? AND tenant_id = ?",
                    (status, utc_now_iso(), alert_id, tenant_id),
                )

    # ---- Incidents ----
    def insert_incident(self, inc: Dict[str, Any]):
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    incident_id, tenant_id, title, severity, status,
                    root_cause_hypothesis, confidence_pct, confidence_explanation,
                    impact, evidence_json, related_alert_ids_json, recommendations_json,
                    created_at, updated_at
                ) VALUES (
                    :incident_id, :tenant_id, :title, :severity, :status,
                    :root_cause_hypothesis, :confidence_pct, :confidence_explanation,
                    :impact, :evidence_json, :related_alert_ids_json, :recommendations_json,
                    :created_at, :updated_at
                )
                """,
                inc,
            )

    def get_incidents(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM incidents WHERE tenant_id = ? ORDER BY updated_at DESC",
                (tenant_id,),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["evidence"] = json.loads(d["evidence_json"])
                d["related_alert_ids"] = json.loads(d["related_alert_ids_json"])
                d["recommendations"] = json.loads(d["recommendations_json"])
                result.append(d)
            return result

    # ---- Anomalies ----
    def insert_anomaly(self, anom: Dict[str, Any]):
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO anomalies (
                    anomaly_id, tenant_id, source_id, metric, current_value,
                    expected_baseline, anomaly_score, severity, method, explanation, timestamp
                ) VALUES (
                    :anomaly_id, :tenant_id, :source_id, :metric, :current_value,
                    :expected_baseline, :anomaly_score, :severity, :method, :explanation, :timestamp
                )
                """,
                anom,
            )

    def get_anomalies(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM anomalies WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- Privacy Audit ----
    def get_last_chain_hash(self, tenant_id: str) -> str:
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT chain_hash FROM privacy_audit WHERE tenant_id = ? ORDER BY rowid DESC LIMIT 1",
                (tenant_id,),
            ).fetchone()
            return row["chain_hash"] if (row and row["chain_hash"]) else ("0" * 64)

    def insert_privacy_audit(self, record: Dict[str, Any]):
        rec = dict(record)
        rec.setdefault("payload_hmac", "")
        rec.setdefault("prev_hash", "")
        rec.setdefault("chain_hash", "")
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO privacy_audit (
                    audit_id, event_id, tenant_id, source_id, timestamp,
                    raw_telemetry_json, sanitized_payload_json, allowed_fields_json,
                    rejected_fields_json, redacted_fields_json, payload_size_bytes,
                    policy_status, transmission_status, payload_hmac, prev_hash, chain_hash
                ) VALUES (
                    :audit_id, :event_id, :tenant_id, :source_id, :timestamp,
                    :raw_telemetry_json, :sanitized_payload_json, :allowed_fields_json,
                    :rejected_fields_json, :redacted_fields_json, :payload_size_bytes,
                    :policy_status, :transmission_status, :payload_hmac, :prev_hash, :chain_hash
                )
                """,
                rec,
            )

    def get_privacy_audits_chronological(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM privacy_audit WHERE tenant_id = ? ORDER BY rowid ASC",
                (tenant_id,),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["raw_telemetry"] = json.loads(d["raw_telemetry_json"])
                d["sanitized_payload"] = json.loads(d["sanitized_payload_json"])
                d["allowed_fields"] = json.loads(d["allowed_fields_json"])
                d["rejected_fields"] = json.loads(d["rejected_fields_json"])
                d["redacted_fields"] = json.loads(d["redacted_fields_json"])
                result.append(d)
            return result

    def get_privacy_audits(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM privacy_audit WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["raw_telemetry"] = json.loads(d["raw_telemetry_json"])
                d["sanitized_payload"] = json.loads(d["sanitized_payload_json"])
                d["allowed_fields"] = json.loads(d["allowed_fields_json"])
                d["rejected_fields"] = json.loads(d["rejected_fields_json"])
                d["redacted_fields"] = json.loads(d["redacted_fields_json"])
                result.append(d)
            return result

    # ---- Local Buffer ----
    def buffer_event(self, event_id: str, tenant_id: str, source_id: str, payload: Dict[str, Any]) -> bool:
        with self.get_conn() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO local_buffer (event_id, tenant_id, source_id, payload_json, created_at, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
                """,
                (event_id, tenant_id, source_id, json.dumps(payload), utc_now_iso()),
            )
            return cur.rowcount > 0

    def get_buffered_events(self, tenant_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        q = "SELECT * FROM local_buffer WHERE 1=1"
        params: List[Any] = []
        if tenant_id:
            q += " AND tenant_id = ?"
            params.append(tenant_id)
        if status:
            q += " AND status = ?"
            params.append(status)
        q += " ORDER BY created_at ASC"
        with self.get_conn() as conn:
            rows = conn.execute(q, params).fetchall()
            res = []
            for r in rows:
                d = dict(r)
                d["payload"] = json.loads(d["payload_json"])
                res.append(d)
            return res

    def mark_buffer_delivered(self, event_id: str):
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE local_buffer SET status = 'DELIVERED', delivered_at = ? WHERE event_id = ?",
                (utc_now_iso(), event_id),
            )

    # ---- Autonomous Actions ----
    def insert_autonomous_action(self, action: Dict[str, Any]):
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO autonomous_actions (
                    action_id, tenant_id, source_id, incident_id, proposed_action,
                    reason, evidence, expected_outcome, risk_level, reversibility,
                    approval_status, execution_status, approved_by, created_at, updated_at
                ) VALUES (
                    :action_id, :tenant_id, :source_id, :incident_id, :proposed_action,
                    :reason, :evidence, :expected_outcome, :risk_level, :reversibility,
                    :approval_status, :execution_status, :approved_by, :created_at, :updated_at
                )
                """,
                action,
            )

    def get_autonomous_actions(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM autonomous_actions WHERE tenant_id = ? ORDER BY updated_at DESC",
                (tenant_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_autonomous_action(
        self,
        action_id: str,
        tenant_id: str,
        approval_status: Optional[str] = None,
        execution_status: Optional[str] = None,
        approved_by: Optional[str] = None,
    ):
        sets = ["updated_at = ?"]
        params: List[Any] = [utc_now_iso()]
        if approval_status is not None:
            sets.append("approval_status = ?")
            params.append(approval_status)
        if execution_status is not None:
            sets.append("execution_status = ?")
            params.append(execution_status)
        if approved_by is not None:
            sets.append("approved_by = ?")
            params.append(approved_by)
        params.extend([action_id, tenant_id])
        with self.get_conn() as conn:
            conn.execute(
                f"UPDATE autonomous_actions SET {', '.join(sets)} WHERE action_id = ? AND tenant_id = ?",
                params,
            )
