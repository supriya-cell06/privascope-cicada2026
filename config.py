"""Central configuration for PRIVASCOPE."""
import os
from pathlib import Path

APP_NAME = "PRIVASCOPE"
APP_SUBTITLE = "Privacy-First Intelligent Observability & AIOps Platform"
APP_VERSION = "1.0.0-cicada2026"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("PRIVASCOPE_DB_PATH", str(BASE_DIR / "privascope.db"))

TENANTS = ["Tenant Alpha", "Tenant Beta", "Tenant Gamma"]
REGIONS = ["Bengaluru", "Mumbai", "Singapore", "Frankfurt", "Virginia"]
ENVIRONMENTS = ["Production", "Staging", "DR"]

REGION_TIMEZONES = {
    "Bengaluru": "Asia/Kolkata (UTC+05:30)",
    "Mumbai": "Asia/Kolkata (UTC+05:30)",
    "Singapore": "Asia/Singapore (UTC+08:00)",
    "Frankfurt": "Europe/Berlin (UTC+01:00)",
    "Virginia": "America/New_York (UTC-05:00)",
}

# Strict Allow-List for outbound cloud metadata (Tier 1 -> Tier 2)
OUTBOUND_ALLOW_LIST = frozenset({
    "event_id",
    "timestamp",
    "source_timezone",
    "tenant_id",
    "source_id",
    "region",
    "environment",
    "event_category",
    "event_type",
    "metric_name",
    "metric_value",
    "cpu_pct",
    "memory_pct",
    "disk_pct",
    "network_mbps",
    "inbound_mbps",
    "outbound_mbps",
    "latency_ms",
    "packet_loss_pct",
    "response_time_ms",
    "error_rate_pct",
    "severity",
    "health_state",
    "sanitized_summary",
    "failed_attempts",
    "anomaly_score",
    "collector_id",
    "collector_health",
})

# Explicitly prohibited sensitive field patterns (defense-in-depth)
SENSITIVE_KEY_PATTERNS = (
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private_key", "ssn", "email", "phone", "credit_card",
    "raw_log", "raw_payload", "request_body", "payload", "user", "username",
    "ip", "client_ip", "source_ip", "customer", "pii", "cookie", "session",
)

# Default monitoring thresholds
DEFAULT_THRESHOLDS = {
    "cpu_warning": 75.0,
    "cpu_critical": 90.0,
    "memory_warning": 78.0,
    "memory_critical": 92.0,
    "disk_warning": 80.0,
    "disk_critical": 95.0,
    "latency_warning_ms": 150.0,
    "latency_critical_ms": 350.0,
    "packet_loss_warning_pct": 1.5,
    "packet_loss_critical_pct": 5.0,
    "stale_seconds": 60,
    "collector_offline_seconds": 60,
}

# Hackathon performance targets (clearly labeled as prototype/simulated)
PERFORMANCE_TARGETS = {
    "collection_to_dashboard_p95_sec": 10.0,
    "threshold_breach_to_alert_sec": 15.0,
    "collector_offline_detection_sec": 60.0,
    "buffered_delivery_loss_pct": 0.0,
    "buffered_delivery_duplicates": 0,
}
