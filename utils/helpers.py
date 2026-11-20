"""General helper functions for PRIVASCOPE."""
import uuid
import json
from typing import Any


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str, sort_keys=True)


def payload_size_bytes(obj: Any) -> int:
    return len(json.dumps(obj, default=str).encode("utf-8"))


def severity_rank(severity: str) -> int:
    ranks = {
        "CRITICAL": 5,
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "INFO": 1,
        "INFORMATIONAL": 1,
    }
    return ranks.get(str(severity).upper(), 0)


def health_color(health: str) -> str:
    mapping = {
        "EXCELLENT": "#10B981",
        "GOOD": "#3B82F6",
        "FAIR": "#F59E0B",
        "POOR": "#EF4444",
        "ONLINE": "#10B981",
        "DEGRADED": "#F59E0B",
        "OFFLINE": "#EF4444",
        "STALE": "#A855F7",
    }
    return mapping.get(str(health).upper(), "#64748B")


def severity_color(severity: str) -> str:
    mapping = {
        "CRITICAL": "#EF4444",
        "HIGH": "#F97316",
        "MEDIUM": "#F59E0B",
        "LOW": "#3B82F6",
        "INFO": "#64748B",
        "INFORMATIONAL": "#64748B",
    }
    return mapping.get(str(severity).upper(), "#64748B")
