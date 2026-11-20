"""Seed infrastructure inventory per tenant across 5 global regions."""
from typing import Any, Dict, List

from config import REGION_TIMEZONES
from utils.timestamps import utc_now_iso

TENANT_BLUEPRINTS = {
    "Tenant Alpha": [
        ("APP-01", "Core Payments API", "Application", "Production", "Bengaluru"),
        ("DB-01", "Primary Ledger DB", "Database", "Production", "Bengaluru"),
        ("VM-01", "Analytics Worker VM", "Virtual Machine", "Production", "Mumbai"),
        ("CTR-01", "Auth Gateway Container", "Container", "Production", "Singapore"),
        ("NET-01", "Edge Router BLR-01", "Network Device", "Production", "Bengaluru"),
        ("CLD-01", "EU Compliance Node", "Cloud Resource", "DR", "Frankfurt"),
    ],
    "Tenant Beta": [
        ("BETA-APP-01", "Retail Checkout Svc", "Application", "Production", "Mumbai"),
        ("BETA-DB-01", "Inventory Postgres", "Database", "Production", "Singapore"),
        ("BETA-SRV-01", "Fulfillment Server", "Server", "Production", "Virginia"),
        ("BETA-NET-01", "Core Switch SG-02", "Network Device", "Production", "Singapore"),
        ("BETA-CTR-01", "Search Indexer Pod", "Container", "Staging", "Frankfurt"),
    ],
    "Tenant Gamma": [
        ("GAMMA-APP-01", "Telehealth Portal", "Application", "Production", "Virginia"),
        ("GAMMA-DB-01", "Records Vault DB", "Database", "Production", "Frankfurt"),
        ("GAMMA-VM-01", "Imaging Pipeline VM", "Virtual Machine", "Production", "Bengaluru"),
        ("GAMMA-NET-01", "WAN Gateway VA-01", "Network Device", "Production", "Virginia"),
        ("GAMMA-DC-01", "Data Center Rack 04", "Data Center", "DR", "Mumbai"),
    ],
}


def build_initial_devices_and_collectors() -> Dict[str, List[Dict[str, Any]]]:
    now = utc_now_iso()
    devices = []
    collectors = []
    for tenant_id, items in TENANT_BLUEPRINTS.items():
        for idx, (src_id, name, dtype, env, region) in enumerate(items, start=1):
            col_id = f"COL-{src_id}"
            devices.append({
                "source_id": src_id,
                "tenant_id": tenant_id,
                "device_name": name,
                "device_type": dtype,
                "environment": env,
                "region": region,
                "source_timezone": REGION_TIMEZONES.get(region, "UTC"),
                "collector_id": col_id,
                "connectivity_status": "CONNECTED",
                "health_status": "EXCELLENT",
                "last_seen": now,
                "cpu_pct": 28.0 + (idx * 3.1) % 15,
                "memory_pct": 42.0 + (idx * 2.7) % 14,
                "disk_pct": 38.0 + (idx * 4.0) % 20,
                "network_mbps": 180.0 + idx * 25.0,
                "inbound_mbps": 100.0 + idx * 14.0,
                "outbound_mbps": 80.0 + idx * 11.0,
                "latency_ms": 22.0 + idx * 4.5,
                "packet_loss_pct": 0.05,
                "response_time_ms": 95.0 + idx * 10.0,
                "error_rate_pct": 0.1,
            })
            collectors.append({
                "collector_id": col_id,
                "tenant_id": tenant_id,
                "source_id": src_id,
                "version": "2.4.1",
                "status": "ONLINE",
                "last_heartbeat": now,
                "cpu_pct": 3.5 + (idx % 4),
                "memory_pct": 16.0 + (idx % 6),
                "config_status": "SYNCED",
                "connectivity": "CONNECTED",
                "collection_status": "ACTIVE",
                "last_transmission": now,
            })
    return {"devices": devices, "collectors": collectors}
