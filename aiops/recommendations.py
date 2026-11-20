"""Explainable AIOps recommendation engine."""
from typing import Any, Dict, List


def generate_recommendation(category: str, source_id: str, evidence: List[str]) -> Dict[str, Any]:
    cat = category.lower()
    if "cpu" in cat:
        return {
            "what_detected": f"Sustained high CPU utilization on {source_id}.",
            "why_it_matters": "CPU saturation queues application threads, increasing response latency and error rates.",
            "evidence": evidence,
            "suggested_next_steps": [
                "Investigate CPU-intensive processes and thread pools.",
                "Check recent deployments or scheduled batch jobs.",
                "Review concurrent workload spikes.",
                "Consider horizontal or vertical scaling if the pattern persists.",
            ],
            "action_risk": "LOW (read-only diagnostics) / MEDIUM (service restart or scaling).",
            "proposed_action": f"Scale compute capacity / restart runaway worker on {source_id}",
        }
    if "memory" in cat:
        return {
            "what_detected": f"Elevated memory consumption on {source_id}.",
            "why_it_matters": "Memory exhaustion triggers garbage collection pauses or OOM kills.",
            "evidence": evidence,
            "suggested_next_steps": [
                "Inspect top memory-consuming processes.",
                "Investigate potential memory leaks in recent application builds.",
                "Review heap and cache sizing limits.",
            ],
            "action_risk": "LOW (heap inspection) / MEDIUM (controlled service restart).",
            "proposed_action": f"Perform controlled cache flush & service restart on {source_id}",
        }
    if "network" in cat or "latency" in cat or "packet" in cat:
        return {
            "what_detected": f"Network degradation (latency/packet loss) affecting {source_id}.",
            "why_it_matters": "Packet loss and high latency degrade inter-service RPCs and end-user responsiveness.",
            "evidence": evidence,
            "suggested_next_steps": [
                "Inspect network congestion and interface error counters.",
                "Check packet loss across upstream switches and gateways.",
                "Validate DNS resolution and routing tables.",
            ],
            "action_risk": "LOW (network diagnostics) / MEDIUM (traffic rerouting).",
            "proposed_action": f"Reroute traffic away from degraded interface on {source_id}",
        }
    if "security" in cat or "auth" in cat:
        return {
            "what_detected": f"Suspicious authentication / security pattern on {source_id}.",
            "why_it_matters": "Repeated failed logins may indicate credential stuffing or brute-force intrusion attempts.",
            "evidence": evidence,
            "suggested_next_steps": [
                "Review authentication activity in local privacy-protected logs.",
                "Verify whether the source is an authorized automation job.",
                "Consider temporarily restricting the offending source after human approval.",
            ],
            "action_risk": "MEDIUM (temporary source restriction may block legitimate users if misclassified).",
            "proposed_action": f"Temporarily rate-limit / block suspicious auth traffic to {source_id}",
        }
    if "collector" in cat:
        return {
            "what_detected": f"Local Privacy Collector heartbeat failure on {source_id}.",
            "why_it_matters": "Loss of collector telemetry creates observability blind spots and stale health states.",
            "evidence": evidence,
            "suggested_next_steps": [
                "Check local collector daemon status and host connectivity.",
                "Inspect local SQLite buffer queue and disk space.",
                "Restart collector agent and verify heartbeat restoration.",
            ],
            "action_risk": "LOW (collector agent restart is non-disruptive to workloads).",
            "proposed_action": f"Clear collector fault and restart agent for {source_id}",
        }
    return {
        "what_detected": f"Operational anomaly detected on {source_id}.",
        "why_it_matters": "Deviation from baseline may precede service degradation.",
        "evidence": evidence,
        "suggested_next_steps": [
            "Inspect recent telemetry trends and correlated alerts.",
            "Verify recent configuration or deployment changes.",
        ],
        "action_risk": "LOW.",
        "proposed_action": f"Run automated health diagnostic check on {source_id}",
    }
