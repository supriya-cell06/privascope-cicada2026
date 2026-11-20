"""Unique Privacy & Secure Communication Engine:
1. HMAC-SHA256 Payload Signing (Tier 1 -> Tier 2 Secure Communication)
2. Tamper-Evident SHA-256 Hash-Chained Egress Audit Ledger
3. Differential Privacy (Laplace Mechanism) for Metric Obfuscation
"""
import hashlib
import hmac
import json
import math
import random
from typing import Any, Dict, List, Tuple

TIER1_SHARED_SECRET = "privascope-tier1-tier2-mtls-hmac-key-2026"
GENESIS_HASH = "0" * 64


def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sign_payload(payload: Dict[str, Any], secret: str = TIER1_SHARED_SECRET) -> str:
    """Generate HMAC-SHA256 signature proving Tier 1 collector authenticity & integrity."""
    msg = canonical_json(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_payload_signature(payload: Dict[str, Any], signature: str, secret: str = TIER1_SHARED_SECRET) -> bool:
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, str(signature or ""))


def compute_chain_hash(prev_hash: str, payload: Dict[str, Any], timestamp: str, event_id: str) -> str:
    """Compute SHA-256 link in the tamper-evident local Egress Audit Ledger."""
    raw = f"{prev_hash}|{event_id}|{timestamp}|{canonical_json(payload)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_audit_chain(audits_chronological: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Verify the entire local Egress Audit hash chain has not been tampered with."""
    if not audits_chronological:
        return True, "Audit ledger is empty (Genesis state valid)."
    prev = GENESIS_HASH
    for idx, rec in enumerate(audits_chronological):
        expected = compute_chain_hash(
            prev,
            rec["sanitized_payload"],
            rec["timestamp"],
            rec["event_id"],
        )
        if rec.get("prev_hash") != prev or rec.get("chain_hash") != expected:
            return False, f"Tampering detected at record #{idx + 1} (Audit ID: {rec['audit_id']})"
        prev = rec["chain_hash"]
    return True, f"Cryptographic integrity verified across all {len(audits_chronological)} egress record(s)."


def apply_differential_privacy(value: float, epsilon: float = 1.0, sensitivity: float = 1.5) -> float:
    """Inject calibrated Laplace noise for epsilon-Differential Privacy."""
    if epsilon <= 0:
        return round(value, 2)
    scale = sensitivity / epsilon
    u = random.uniform(-0.4999, 0.4999)
    noise = -scale * math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u))
    return round(max(0.0, value + noise), 2)
