"""Collector fleet health evaluation with 60-second offline detection target."""
from typing import Any, Dict, List

from database.db import DatabaseManager
from utils.timestamps import seconds_since


def evaluate_collectors(db: DatabaseManager, tenant_id: str) -> List[Dict[str, Any]]:
    thresholds = db.get_thresholds()
    offline_sec = float(thresholds.get("collector_offline_seconds", 60))
    collectors = db.get_collectors(tenant_id)
    result = []
    for c in collectors:
        hb_age = seconds_since(c["last_heartbeat"])
        status = c["status"]
        if status == "OFFLINE" or hb_age >= offline_sec:
            effective_status = "OFFLINE"
        elif hb_age >= offline_sec * 0.65:
            effective_status = "STALE"
        elif c["cpu_pct"] >= 70.0 or c["memory_pct"] >= 80.0 or status == "DEGRADED":
            effective_status = "DEGRADED"
        else:
            effective_status = "ONLINE"

        item = dict(c)
        item["seconds_since_heartbeat"] = round(hb_age, 1)
        item["effective_status"] = effective_status
        result.append(item)
    return result
