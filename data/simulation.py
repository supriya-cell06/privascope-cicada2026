"""Telemetry simulator and 8 predefined Hackathon Demo Scenarios."""
import random
from typing import Any, Dict

from aiops.anomaly_detection import AnomalyDetector
from aiops.correlation import CorrelationEngine
from autonomous_ops.actions import propose_action
from collector.local_collector import LocalPrivacyCollector
from collector.metadata_processor import classify_health
from data.sample_data import build_initial_devices_and_collectors
from database.db import DatabaseManager
from utils.helpers import generate_id
from utils.timestamps import iso_offset, utc_now_iso


SCENARIO_NAMES = [
    "Scenario 1 — Normal Operations",
    "Scenario 2 — CPU Anomaly",
    "Scenario 3 — Security Attack",
    "Scenario 4 — Network Failure",
    "Scenario 5 — SaaS Outage & Local Buffer",
    "Scenario 6 — Multiple Related Alerts",
    "Scenario 7 — Collector Offline",
    "Scenario 8 — Privacy Demonstration",
]


class TelemetrySimulator:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.collector = LocalPrivacyCollector(db)
        self.detector = AnomalyDetector(db)
        self.correlator = CorrelationEngine(db)

    def ensure_seeded(self):
        if not self.db.get_devices("Tenant Alpha"):
            self.seed_baseline()

    def seed_baseline(self):
        self.db.reset_all_data()
        seed = build_initial_devices_and_collectors()
        for d in seed["devices"]:
            self.db.upsert_device(d)
        for c in seed["collectors"]:
            self.db.upsert_collector(c)

        # Generate 10 historical normal points per device across all tenants
        rng = random.Random(42)
        for d in seed["devices"]:
            for step in range(10, 0, -1):
                ts = iso_offset(-step * 60)
                cpu = round(max(10.0, min(55.0, d["cpu_pct"] + rng.uniform(-6, 6))), 1)
                mem = round(max(20.0, min(65.0, d["memory_pct"] + rng.uniform(-5, 5))), 1)
                lat = round(max(12.0, min(65.0, d["latency_ms"] + rng.uniform(-5, 8))), 1)
                loss = round(max(0.0, rng.uniform(0.0, 0.25)), 2)
                in_bw = round(d["inbound_mbps"] + rng.uniform(-15, 18), 1)
                out_bw = round(d["outbound_mbps"] + rng.uniform(-12, 15), 1)
                raw = {
                    "event_id": generate_id("EVT"),
                    "timestamp": ts,
                    "tenant_id": d["tenant_id"],
                    "source_id": d["source_id"],
                    "region": d["region"],
                    "environment": d["environment"],
                    "source_timezone": d["source_timezone"],
                    "event_category": "infrastructure",
                    "event_type": "metric_sample",
                    "cpu_pct": cpu,
                    "memory_pct": mem,
                    "disk_pct": d["disk_pct"],
                    "network_mbps": round(in_bw + out_bw, 1),
                    "inbound_mbps": in_bw,
                    "outbound_mbps": out_bw,
                    "latency_ms": lat,
                    "packet_loss_pct": loss,
                    "response_time_ms": round(80 + lat * 1.4, 1),
                    "error_rate_pct": round(rng.uniform(0.0, 0.3), 2),
                    "collector_id": d["collector_id"],
                    "collector_health": "ONLINE",
                    # Sensitive local fields that MUST be stripped by Tier 1
                    "internal_host_ip": f"10.0.{rng.randint(1,9)}.{rng.randint(10,240)}",
                    "api_key": f"sk-live-local-{rng.randint(10000,99999)}",
                }
                self.collector.process_raw_telemetry(raw)

    def generate_tick(self, tenant_id: str):
        devices = self.db.get_devices(tenant_id)
        now = utc_now_iso()
        for d in devices:
            cpu = round(max(8.0, min(99.0, d["cpu_pct"] + random.uniform(-4.5, 4.5))), 1)
            mem = round(max(15.0, min(98.0, d["memory_pct"] + random.uniform(-3.0, 3.0))), 1)
            lat = round(max(10.0, d["latency_ms"] + random.uniform(-6.0, 7.0)), 1)
            loss = round(max(0.0, d["packet_loss_pct"] + random.uniform(-0.05, 0.08)), 2)
            in_bw = round(max(20.0, d["inbound_mbps"] + random.uniform(-15, 15)), 1)
            out_bw = round(max(15.0, d["outbound_mbps"] + random.uniform(-12, 12)), 1)
            health = classify_health(cpu, mem, d["disk_pct"], lat, loss, d["connectivity_status"])

            raw = {
                "event_id": generate_id("EVT"),
                "timestamp": now,
                "tenant_id": tenant_id,
                "source_id": d["source_id"],
                "region": d["region"],
                "environment": d["environment"],
                "source_timezone": d["source_timezone"],
                "event_category": "infrastructure",
                "event_type": "metric_sample",
                "cpu_pct": cpu,
                "memory_pct": mem,
                "disk_pct": d["disk_pct"],
                "network_mbps": round(in_bw + out_bw, 1),
                "inbound_mbps": in_bw,
                "outbound_mbps": out_bw,
                "latency_ms": lat,
                "packet_loss_pct": loss,
                "response_time_ms": round(80 + lat * 1.3 + (cpu * 0.8), 1),
                "error_rate_pct": round(0.1 if health in ("EXCELLENT", "GOOD") else random.uniform(1.2, 4.8), 2),
                "health_state": health,
                "collector_id": d["collector_id"],
                "collector_health": "ONLINE",
                "auth_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.LOCAL_ONLY",
            }
            self.collector.process_raw_telemetry(raw)

            d_upd = dict(d)
            d_upd.update({
                "cpu_pct": cpu, "memory_pct": mem, "latency_ms": lat,
                "packet_loss_pct": loss, "network_mbps": round(in_bw + out_bw, 1),
                "inbound_mbps": in_bw, "outbound_mbps": out_bw,
                "health_status": health, "last_seen": now,
            })
            self.db.upsert_device(d_upd)

    def trigger_cpu_anomaly(self, tenant_id: str) -> Dict[str, Any]:
        devices = self.db.get_devices(tenant_id)
        target = devices[0]
        now = utc_now_iso()
        raw = {
            "event_id": generate_id("EVT"),
            "timestamp": now,
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "region": target["region"],
            "environment": target["environment"],
            "source_timezone": target["source_timezone"],
            "event_category": "infrastructure",
            "event_type": "cpu_spike",
            "cpu_pct": 95.4,
            "memory_pct": 79.2,
            "disk_pct": target["disk_pct"],
            "network_mbps": 420.0,
            "inbound_mbps": 230.0,
            "outbound_mbps": 190.0,
            "latency_ms": 265.0,
            "packet_loss_pct": 0.4,
            "response_time_ms": 1850.0,
            "error_rate_pct": 4.2,
            "severity": "CRITICAL",
            "health_state": "POOR",
            "collector_id": target["collector_id"],
            "collector_health": "ONLINE",
            "raw_payload": "POST /api/v1/checkout user_email=customer@example.com",
            "secret_key": "prod-secret-998877",
        }
        res = self.collector.process_raw_telemetry(raw)
        upd = dict(target)
        upd.update({
            "cpu_pct": 95.4, "memory_pct": 79.2, "latency_ms": 265.0,
            "response_time_ms": 1850.0, "error_rate_pct": 4.2,
            "health_status": "POOR", "last_seen": now,
        })
        self.db.upsert_device(upd)

        self.db.upsert_alert({
            "alert_id": generate_id("ALT"),
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "event_id": raw["event_id"],
            "category": "infrastructure",
            "title": f"Critical CPU Utilization on {target['source_id']}",
            "description": f"CPU surged to 95.4% with response latency at 1850ms.",
            "severity": "CRITICAL",
            "status": "OPEN",
            "assigned_to": "Unassigned",
            "occurrence_count": 1,
            "created_at": now,
            "updated_at": now,
            "detection_latency_sec": 1.4,
        })
        self.detector.detect_for_tenant(tenant_id)
        incidents = self.correlator.correlate_alerts(tenant_id)
        propose_action(
            self.db, tenant_id, target["source_id"],
            proposed_action=f"Scale compute workers & restart runaway thread pool on {target['source_id']}",
            reason="CPU utilization reached 95.4% causing 1.85s response latency.",
            evidence="CPU=95.4%, Response Time=1850ms, Error Rate=4.2%",
            expected_outcome="CPU stabilizes below 50% and latency returns under 150ms.",
            risk_level="MEDIUM",
            incident_id=incidents[0]["incident_id"] if incidents else None,
        )
        return res

    def trigger_security_event(self, tenant_id: str) -> Dict[str, Any]:
        devices = self.db.get_devices(tenant_id)
        target = next((d for d in devices if "DB" in d["source_id"]), devices[0])
        now = utc_now_iso()
        raw = {
            "event_id": generate_id("EVT"),
            "timestamp": now,
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "region": target["region"],
            "environment": target["environment"],
            "source_timezone": target["source_timezone"],
            "event_category": "security",
            "event_type": "repeated_authentication_failure",
            "failed_attempts": 25,
            "severity": "HIGH",
            "health_state": "POOR",
            "collector_id": target["collector_id"],
            "collector_health": "ONLINE",
            # STRICTLY LOCAL SENSITIVE DATA
            "USERNAME": "admin",
            "PASSWORD": "Admin@123",
            "IP": "192.168.1.50",
            "REQUEST": "/admin/login",
            "RAW_LOG": "2026-11-20 14:45:12 SERVER=DB-01 USER=admin PASSWORD=Admin@123 FAILED_LOGIN_ATTEMPTS=25 IP=192.168.1.50",
            "API_KEY": "ak_live_9182736455_secret",
        }
        res = self.collector.process_raw_telemetry(raw)
        upd = dict(target)
        upd.update({"health_status": "POOR", "last_seen": now})
        self.db.upsert_device(upd)

        self.db.upsert_alert({
            "alert_id": generate_id("ALT"),
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "event_id": raw["event_id"],
            "category": "security",
            "title": f"Repeated Authentication Failures on {target['source_id']}",
            "description": "25 failed login attempts detected within 60 seconds. Raw credentials redacted locally.",
            "severity": "HIGH",
            "status": "OPEN",
            "assigned_to": "SOC-Tier1",
            "occurrence_count": 1,
            "created_at": now,
            "updated_at": now,
            "detection_latency_sec": 0.9,
        })
        incidents = self.correlator.correlate_alerts(tenant_id)
        propose_action(
            self.db, tenant_id, target["source_id"],
            proposed_action=f"Temporarily rate-limit suspicious authentication source targeting {target['source_id']}",
            reason="25 consecutive failed login attempts indicate probable brute-force activity.",
            evidence="event_type=repeated_authentication_failure, failed_attempts=25, severity=HIGH",
            expected_outcome="Stops unauthorized login flood while preserving authorized session tokens.",
            risk_level="MEDIUM",
            incident_id=incidents[0]["incident_id"] if incidents else None,
        )
        return res

    def trigger_network_issue(self, tenant_id: str, outage: bool = False) -> Dict[str, Any]:
        devices = self.db.get_devices(tenant_id)
        target = next((d for d in devices if "NET" in d["source_id"]), devices[-1])
        now = utc_now_iso()
        lat = 620.0 if not outage else 0.0
        loss = 8.4 if not outage else 100.0
        conn = "DEGRADED" if not outage else "DISCONNECTED"
        raw = {
            "event_id": generate_id("EVT"),
            "timestamp": now,
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "region": target["region"],
            "environment": target["environment"],
            "source_timezone": target["source_timezone"],
            "event_category": "network",
            "event_type": "network_outage" if outage else "high_latency_packet_loss",
            "cpu_pct": 54.0,
            "memory_pct": 61.0,
            "disk_pct": target["disk_pct"],
            "network_mbps": 0.0 if outage else 940.0,
            "inbound_mbps": 0.0 if outage else 520.0,
            "outbound_mbps": 0.0 if outage else 420.0,
            "latency_ms": lat,
            "packet_loss_pct": loss,
            "response_time_ms": 2400.0,
            "error_rate_pct": 12.5,
            "severity": "CRITICAL",
            "health_state": "POOR",
            "collector_id": target["collector_id"],
            "collector_health": "ONLINE",
            "client_ip": "172.16.44.19",
        }
        res = self.collector.process_raw_telemetry(raw)
        upd = dict(target)
        upd.update({
            "latency_ms": lat, "packet_loss_pct": loss,
            "network_mbps": raw["network_mbps"], "inbound_mbps": raw["inbound_mbps"],
            "outbound_mbps": raw["outbound_mbps"], "connectivity_status": conn,
            "health_status": "POOR", "last_seen": now,
        })
        self.db.upsert_device(upd)

        self.db.upsert_alert({
            "alert_id": generate_id("ALT"),
            "tenant_id": tenant_id,
            "source_id": target["source_id"],
            "event_id": raw["event_id"],
            "category": "network",
            "title": f"Severe Network Degradation on {target['source_id']}",
            "description": f"Latency={lat}ms, Packet Loss={loss}%, Bandwidth Spike detected.",
            "severity": "CRITICAL",
            "status": "OPEN",
            "assigned_to": "NetOps",
            "occurrence_count": 1,
            "created_at": now,
            "updated_at": now,
            "detection_latency_sec": 1.1,
        })
        self.detector.detect_for_tenant(tenant_id)
        self.correlator.correlate_alerts(tenant_id)
        return res

    def trigger_multiple_related_alerts(self, tenant_id: str):
        devices = self.db.get_devices(tenant_id)
        target = devices[0]
        now = utc_now_iso()
        self.trigger_cpu_anomaly(tenant_id)
        alerts_to_add = [
            ("application", f"Elevated Response Latency on {target['source_id']}", "Application response time reached 2.4 seconds.", "HIGH"),
            ("network", f"Elevated Network Latency on {target['source_id']}", "Upstream network latency rose to 265ms.", "HIGH"),
            ("application", f"Increased HTTP 5xx Error Rate on {target['source_id']}", "Failed request rate climbed to 6.8%.", "CRITICAL"),
        ]
        for cat, title, desc, sev in alerts_to_add:
            self.db.upsert_alert({
                "alert_id": generate_id("ALT"),
                "tenant_id": tenant_id,
                "source_id": target["source_id"],
                "event_id": generate_id("EVT"),
                "category": cat,
                "title": title,
                "description": desc,
                "severity": sev,
                "status": "OPEN",
                "assigned_to": "SRE-OnCall",
                "occurrence_count": 1,
                "created_at": now,
                "updated_at": now,
                "detection_latency_sec": 1.8,
            })
        self.correlator.correlate_alerts(tenant_id)

    def trigger_collector_offline(self, tenant_id: str):
        collectors = self.db.get_collectors(tenant_id)
        devices = self.db.get_devices(tenant_id)
        if not collectors:
            return
        col = dict(collectors[0])
        stale_ts = iso_offset(-95)  # 95 seconds ago -> exceeds 60s target
        col.update({
            "status": "OFFLINE",
            "last_heartbeat": stale_ts,
            "connectivity": "DISCONNECTED",
            "collection_status": "STOPPED",
        })
        self.db.upsert_collector(col)

        dev = next((d for d in devices if d["source_id"] == col["source_id"]), None)
        if dev:
            dev_upd = dict(dev)
            dev_upd.update({"last_seen": stale_ts, "health_status": "POOR", "connectivity_status": "STALE"})
            self.db.upsert_device(dev_upd)

        now = utc_now_iso()
        self.db.upsert_alert({
            "alert_id": generate_id("ALT"),
            "tenant_id": tenant_id,
            "source_id": col["source_id"],
            "event_id": generate_id("EVT"),
            "category": "collector",
            "title": f"Collector Offline: {col['collector_id']}",
            "description": f"No heartbeat received from {col['collector_id']} for >60s. Telemetry is STALE.",
            "severity": "CRITICAL",
            "status": "OPEN",
            "assigned_to": "Platform-Ops",
            "occurrence_count": 1,
            "created_at": now,
            "updated_at": now,
            "detection_latency_sec": 12.0,
        })
        self.correlator.correlate_alerts(tenant_id)
        propose_action(
            self.db, tenant_id, col["source_id"],
            proposed_action=f"Clear collector fault and restart {col['collector_id']}",
            reason="Collector missed heartbeat threshold (>60s) causing stale telemetry.",
            evidence=f"collector_id={col['collector_id']}, last_heartbeat={stale_ts}",
            expected_outcome="Collector returns ONLINE and resumes streaming sanitized metadata.",
            risk_level="LOW",
        )

    def run_scenario(self, scenario_name: str, tenant_id: str):
        self.db.set_state("active_scenario", scenario_name)
        if "Scenario 1" in scenario_name:
            self.seed_baseline()
        elif "Scenario 2" in scenario_name:
            self.seed_baseline()
            self.trigger_cpu_anomaly(tenant_id)
        elif "Scenario 3" in scenario_name:
            self.seed_baseline()
            self.trigger_security_event(tenant_id)
        elif "Scenario 4" in scenario_name:
            self.seed_baseline()
            self.trigger_network_issue(tenant_id, outage=False)
        elif "Scenario 5" in scenario_name:
            self.seed_baseline()
            self.collector.transmitter.set_saas_online(False)
            self.generate_tick(tenant_id)
            self.trigger_security_event(tenant_id)
        elif "Scenario 6" in scenario_name:
            self.seed_baseline()
            self.trigger_multiple_related_alerts(tenant_id)
        elif "Scenario 7" in scenario_name:
            self.seed_baseline()
            self.trigger_collector_offline(tenant_id)
        elif "Scenario 8" in scenario_name:
            self.seed_baseline()
            self.trigger_security_event(tenant_id)
