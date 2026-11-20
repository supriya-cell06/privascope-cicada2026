"""Network monitoring and impact analysis."""
from typing import Any, Dict, List

from database.db import DatabaseManager


def get_network_summary(db: DatabaseManager, tenant_id: str) -> Dict[str, Any]:
    devices = db.get_devices(tenant_id)
    if not devices:
        return {
            "avg_latency_ms": 0.0,
            "avg_packet_loss_pct": 0.0,
            "total_bandwidth_mbps": 0.0,
            "degraded_links": 0,
            "impact_summary": "No monitored network interfaces.",
        }
    avg_lat = sum(d["latency_ms"] for d in devices) / len(devices)
    avg_loss = sum(d["packet_loss_pct"] for d in devices) / len(devices)
    total_bw = sum(d["network_mbps"] for d in devices)
    degraded = [d for d in devices if d["latency_ms"] >= 150 or d["packet_loss_pct"] >= 1.5 or d["connectivity_status"] != "CONNECTED"]

    if any(d["connectivity_status"] != "CONNECTED" for d in devices):
        impact = "CRITICAL: Network outage detected. Dependent applications may experience complete request failures."
    elif avg_loss >= 2.0 or avg_lat >= 250:
        impact = "HIGH: Elevated packet loss and latency causing TCP retransmissions and degraded user response times."
    elif degraded:
        impact = f"MODERATE: {len(degraded)} node(s) showing elevated latency or packet loss; monitor upstream links."
    else:
        impact = "HEALTHY: Network latency, throughput, and packet delivery are within normal operating baselines."

    return {
        "avg_latency_ms": round(avg_lat, 1),
        "avg_packet_loss_pct": round(avg_loss, 2),
        "total_bandwidth_mbps": round(total_bw, 1),
        "degraded_links": len(degraded),
        "impact_summary": impact,
    }
