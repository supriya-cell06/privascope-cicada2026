"""Infrastructure health evaluation and stale telemetry detection."""
from typing import Any, Dict, List

from collector.metadata_processor import classify_health
from database.db import DatabaseManager
from utils.timestamps import seconds_since


def evaluate_devices(db: DatabaseManager, tenant_id: str) -> List[Dict[str, Any]]:
    thresholds = db.get_thresholds()
    stale_limit = float(thresholds.get("stale_seconds", 60))
    devices = db.get_devices(tenant_id)
    evaluated = []
    for d in devices:
        age_sec = seconds_since(d["last_seen"])
        is_stale = age_sec > stale_limit
        health = classify_health(
            cpu_pct=d["cpu_pct"],
            memory_pct=d["memory_pct"],
            disk_pct=d["disk_pct"],
            latency_ms=d["latency_ms"],
            packet_loss_pct=d["packet_loss_pct"],
            connectivity=d["connectivity_status"],
            is_stale=is_stale,
            thresholds=thresholds,
        )
        item = dict(d)
        item["age_seconds"] = round(age_sec, 1)
        item["is_stale"] = is_stale
        item["health_status"] = health
        item["health_display"] = f"{health} (STALE)" if is_stale else health
        evaluated.append(item)
    return evaluated
