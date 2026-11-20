"""Incident Correlation Engine: Groups related alerts into explainable incidents."""
import json
from typing import Any, Dict, List

from aiops.recommendations import generate_recommendation
from database.db import DatabaseManager
from utils.helpers import generate_id, severity_rank
from utils.timestamps import utc_now_iso


class CorrelationEngine:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def correlate_alerts(self, tenant_id: str) -> List[Dict[str, Any]]:
        open_alerts = [a for a in self.db.get_alerts(tenant_id) if a["status"] != "RESOLVED"]
        if not open_alerts:
            return []

        by_source: Dict[str, List[Dict[str, Any]]] = {}
        for alert in open_alerts:
            by_source.setdefault(alert["source_id"], []).append(alert)

        created_incidents: List[Dict[str, Any]] = []
        now = utc_now_iso()

        for source_id, alerts in by_source.items():
            # Correlate if 2+ alerts on same source OR 1 CRITICAL/HIGH alert
            top_sev = max(alerts, key=lambda a: severity_rank(a["severity"]))["severity"]
            if len(alerts) < 2 and severity_rank(top_sev) < 4:
                continue

            categories = {a["category"].lower() for a in alerts}
            titles = " | ".join(a["title"] for a in alerts)
            evidence = [f"[{a['severity']}] {a['title']}: {a['description']}" for a in alerts]

            if "security" in categories:
                title = f"Security Threat & Suspicious Access on {source_id}"
                root_cause = f"Repeated authentication failures or unauthorized access targeting {source_id}."
                rec_cat = "security"
                impact = "Potential credential compromise or brute-force attack against protected services."
            elif "collector" in categories:
                title = f"Collector Availability & Stale Telemetry on {source_id}"
                root_cause = f"Local Privacy Collector heartbeat lost for {source_id}, causing stale visibility."
                rec_cat = "collector"
                impact = "Observability blind spot; real-time anomaly detection degraded for this source."
            elif "network" in categories and len(alerts) >= 2:
                title = f"Network-Induced Application Degradation on {source_id}"
                root_cause = f"Elevated network latency and packet loss impacting application responsiveness on {source_id}."
                rec_cat = "network"
                impact = "Increased request latency, TCP retransmissions, and elevated application error rates."
            elif "cpu" in titles.lower():
                title = f"Application Performance Degradation on {source_id}"
                root_cause = f"Sustained high CPU utilization on {source_id} driving response latency and errors."
                rec_cat = "cpu"
                impact = "Degraded user experience and elevated service response times."
            else:
                title = f"Correlated Multi-Signal Degradation on {source_id}"
                root_cause = f"Multiple concurrent telemetry anomalies detected on {source_id}."
                rec_cat = "infrastructure"
                impact = "Potential service instability requiring operator investigation."

            confidence = min(96.0, 62.0 + len(alerts) * 11.0)
            conf_expl = (
                f"Confidence is {confidence:.0f}% based on {len(alerts)} correlated signal(s) "
                f"across {', '.join(sorted(categories))} on {source_id} within the active correlation window."
            )
            rec = generate_recommendation(rec_cat, source_id, evidence)

            inc_id = f"INC-{tenant_id.split()[-1].upper()}-{source_id}"
            incident = {
                "incident_id": inc_id,
                "tenant_id": tenant_id,
                "title": title,
                "severity": top_sev,
                "status": "OPEN",
                "root_cause_hypothesis": root_cause,
                "confidence_pct": confidence,
                "confidence_explanation": conf_expl,
                "impact": impact,
                "evidence_json": json.dumps(evidence),
                "related_alert_ids_json": json.dumps([a["alert_id"] for a in alerts]),
                "recommendations_json": json.dumps(rec),
                "created_at": now,
                "updated_at": now,
            }
            self.db.insert_incident(incident)
            created_incidents.append(incident)

        return created_incidents
