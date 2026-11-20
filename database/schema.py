"""SQLite schema definition for PRIVASCOPE."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'Enterprise',
    region_primary TEXT NOT NULL DEFAULT 'Bengaluru',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    source_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    environment TEXT NOT NULL,
    region TEXT NOT NULL,
    source_timezone TEXT NOT NULL,
    collector_id TEXT NOT NULL,
    connectivity_status TEXT NOT NULL DEFAULT 'CONNECTED',
    health_status TEXT NOT NULL DEFAULT 'EXCELLENT',
    last_seen TEXT NOT NULL,
    cpu_pct REAL DEFAULT 0.0,
    memory_pct REAL DEFAULT 0.0,
    disk_pct REAL DEFAULT 0.0,
    network_mbps REAL DEFAULT 0.0,
    inbound_mbps REAL DEFAULT 0.0,
    outbound_mbps REAL DEFAULT 0.0,
    latency_ms REAL DEFAULT 0.0,
    packet_loss_pct REAL DEFAULT 0.0,
    response_time_ms REAL DEFAULT 0.0,
    error_rate_pct REAL DEFAULT 0.0,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE IF NOT EXISTS telemetry (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source_timezone TEXT NOT NULL,
    event_category TEXT NOT NULL,
    event_type TEXT NOT NULL,
    cpu_pct REAL,
    memory_pct REAL,
    disk_pct REAL,
    network_mbps REAL,
    inbound_mbps REAL,
    outbound_mbps REAL,
    latency_ms REAL,
    packet_loss_pct REAL,
    response_time_ms REAL,
    error_rate_pct REAL,
    failed_attempts INTEGER DEFAULT 0,
    severity TEXT DEFAULT 'INFO',
    health_state TEXT DEFAULT 'EXCELLENT',
    anomaly_score REAL DEFAULT 0.0,
    sanitized_summary TEXT,
    ingested_at TEXT NOT NULL,
    processing_latency_ms REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS collectors (
    collector_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '2.4.1',
    status TEXT NOT NULL DEFAULT 'ONLINE',
    last_heartbeat TEXT NOT NULL,
    cpu_pct REAL DEFAULT 4.2,
    memory_pct REAL DEFAULT 18.5,
    config_status TEXT NOT NULL DEFAULT 'SYNCED',
    connectivity TEXT NOT NULL DEFAULT 'CONNECTED',
    collection_status TEXT NOT NULL DEFAULT 'ACTIVE',
    last_transmission TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    event_id TEXT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    assigned_to TEXT DEFAULT 'Unassigned',
    occurrence_count INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    detection_latency_sec REAL DEFAULT 1.2
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    root_cause_hypothesis TEXT NOT NULL,
    confidence_pct REAL NOT NULL,
    confidence_explanation TEXT NOT NULL,
    impact TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    related_alert_ids_json TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    current_value REAL NOT NULL,
    expected_baseline REAL NOT NULL,
    anomaly_score REAL NOT NULL,
    severity TEXT NOT NULL,
    method TEXT NOT NULL,
    explanation TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS privacy_audit (
    audit_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    raw_telemetry_json TEXT NOT NULL,
    sanitized_payload_json TEXT NOT NULL,
    allowed_fields_json TEXT NOT NULL,
    rejected_fields_json TEXT NOT NULL,
    redacted_fields_json TEXT NOT NULL,
    payload_size_bytes INTEGER NOT NULL,
    policy_status TEXT NOT NULL,
    transmission_status TEXT NOT NULL,
    payload_hmac TEXT DEFAULT '',
    prev_hash TEXT DEFAULT '',
    chain_hash TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS local_buffer (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    retry_count INTEGER DEFAULT 0,
    delivered_at TEXT
);

CREATE TABLE IF NOT EXISTS autonomous_actions (
    action_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    incident_id TEXT,
    proposed_action TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence TEXT NOT NULL,
    expected_outcome TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    reversibility TEXT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'PENDING',
    execution_status TEXT NOT NULL DEFAULT 'NOT_EXECUTED',
    approved_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_tenant_ts ON telemetry(tenant_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts(tenant_id, severity);
CREATE INDEX IF NOT EXISTS idx_incidents_tenant ON incidents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_privacy_tenant ON privacy_audit(tenant_id, timestamp);
"""
