"""Tier 1 Privacy Filter: Strict Allow-List, Sensitive Field Detection & Redaction."""
import re
from typing import Any, Dict, List, Tuple

from config import OUTBOUND_ALLOW_LIST, SENSITIVE_KEY_PATTERNS

# Regex patterns to catch accidental leakage inside string values
VALUE_SECRET_PATTERNS = [
    (re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+"), "[REDACTED_PASSWORD]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|bearer)\s*[:=]?\s*[A-Za-z0-9_\-\.]{8,}"), "[REDACTED_SECRET]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
]


def is_sensitive_key(key: str) -> bool:
    k_lower = str(key).lower().strip()
    return any(pat in k_lower for pat in SENSITIVE_KEY_PATTERNS)


def redact_string_value(val: str) -> Tuple[str, bool]:
    redacted = val
    changed = False
    for pattern, replacement in VALUE_SECRET_PATTERNS:
        new_val = pattern.sub(replacement, redacted)
        if new_val != redacted:
            changed = True
            redacted = new_val
    return redacted, changed


def filter_telemetry(raw_telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actively enforce the Tier 1 privacy boundary.
    - Rejects any field matching sensitive key patterns.
    - Rejects any unknown field not present in OUTBOUND_ALLOW_LIST.
    - Redacts sensitive patterns inside allowed string values (e.g., sanitized_summary).
    Returns sanitized payload plus full audit breakdown.
    """
    sanitized_payload: Dict[str, Any] = {}
    allowed_fields: List[str] = []
    rejected_fields: List[str] = []
    redacted_fields: List[str] = []

    for key, value in raw_telemetry.items():
        if is_sensitive_key(key):
            rejected_fields.append(key)
            continue

        if key not in OUTBOUND_ALLOW_LIST:
            rejected_fields.append(key)
            continue

        if isinstance(value, str):
            clean_val, was_redacted = redact_string_value(value)
            if was_redacted:
                redacted_fields.append(key)
            sanitized_payload[key] = clean_val
        else:
            sanitized_payload[key] = value

        allowed_fields.append(key)

    policy_status = "PASSED_STRICT_ALLOW_LIST"
    for k in list(sanitized_payload.keys()):
        if k not in OUTBOUND_ALLOW_LIST or is_sensitive_key(k):
            del sanitized_payload[k]
            rejected_fields.append(k)
            policy_status = "ENFORCED_WITH_STRIP"

    return {
        "sanitized_payload": sanitized_payload,
        "allowed_fields": sorted(allowed_fields),
        "rejected_fields": sorted(set(rejected_fields)),
        "redacted_fields": sorted(set(redacted_fields)),
        "policy_status": policy_status,
    }
