"""Normalizes raw local telemetry and computes dynamic health classification."""
from typing import Any, Dict

from config import DEFAULT_THRESHOLDS, REGION_TIMEZONES
from utils.helpers import generate_id
from utils.timestamps import utc_now_iso


def classify_health(
    cpu_pct: float = 0.0,
    memory_pct: float = 0.0,
    disk_pct: float = 0.0,
    latency_ms: float = 0.0,
    packet_loss_pct: float = 0.0,
    connectivity: str = "CONNECTED",
    failed_attempts: int = 0,
    is_stale: bool = False,
    thresholds: Dict[str, float] = None,
) -> str:
    th = thresholds or DEFAULT_THRESHOLDS
    if connectivity != "CONNECTED" or is_stale:
        return "POOR"
    if (
        cpu_pct >= th["cpu_critical"]
        or memory_pct >= th["memory_critical"]
        or disk_pct >= th["disk_critical"]
        or latency_ms >= th["latency_critical_ms"]
        or packet_loss_pct >= th["packet_loss_critical_pct"]
        or failed_attempts >= 15
    ):
        return "POOR"
    if (
        cpu_pct >= th["cpu_warning"]
        or memory_pct >= th["memory_warning"]
        or disk_pct >= th["disk_warning"]
        or latency_ms >= th["latency_warning_ms"]
        or packet_loss_pct >= th["packet_loss_warning_pct"]
        or failed_attempts >= 5
    ):
        return "FAIR"
    if (
        cpu_pct >= 55.0
        or memory_pct >= 60.0
        or latency_ms >= 80.0
        or packet_loss_pct >= 0.4
    ):
        return "GOOD"
    return "EXCELLENT"


def normalize_raw_telemetry(raw: Dict[str, Any], thresholds: Dict[str, float] = None) -> Dict[str, Any]:
    """Enrich raw telemetry locally with normalized metadata before privacy filtering."""
    normalized = dict(raw)
    normalized.setdefault("event_id", generate_id("EVT"))
    normalized.setdefault("timestamp", utc_now_iso())
    region = normalized.get("region", "Bengaluru")
    normalized.setdefault("source_timezone", REGION_TIMEZONES.get(region, "UTC"))
    normalized.setdefault("event_category", "infrastructure")
    normalized.setdefault("event_type", "metric_sample")

    cpu = float(normalized.get("cpu_pct") or 0.0)
    mem = float(normalized.get("memory_pct") or 0.0)
    disk = float(normalized.get("disk_pct") or 0.0)
    lat = float(normalized.get("latency_ms") or 0.0)
    loss = float(normalized.get("packet_loss_pct") or 0.0)
    failed = int(normalized.get("failed_attempts") or 0)
    conn = str(normalized.get("connectivity_status") or "CONNECTED")

    if "health_state" not in normalized:
        normalized["health_state"] = classify_health(
            cpu_pct=cpu,
            memory_pct=mem,
            disk_pct=disk,
            latency_ms=lat,
            packet_loss_pct=loss,
            connectivity=conn,
            failed_attempts=failed,
            thresholds=thresholds,
        )

    if "severity" not in normalized:
        if normalized["health_state"] == "POOR":
            normalized["severity"] = "HIGH" if failed < 20 and cpu < 95 else "CRITICAL"
        elif normalized["health_state"] == "FAIR":
            normalized["severity"] = "MEDIUM"
        else:
            normalized["severity"] = "INFO"

    if "sanitized_summary" not in normalized:
        if normalized["event_category"] == "security":
            normalized["sanitized_summary"] = (
                f"Security event {normalized['event_type']} on {normalized.get('source_id', 'UNKNOWN')} "
                f"(attempts={failed}, severity={normalized['severity']})"
            )
        elif normalized["event_category"] == "network":
            normalized["sanitized_summary"] = (
                f"Network telemetry for {normalized.get('source_id', 'UNKNOWN')}: "
                f"latency={lat:.1f}ms, packet_loss={loss:.2f}%"
            )
        else:
            normalized["sanitized_summary"] = (
                f"Telemetry sample for {normalized.get('source_id', 'UNKNOWN')}: "
                f"CPU={cpu:.1f}%, MEM={mem:.1f}%, LAT={lat:.1f}ms"
            )

    return normalized
