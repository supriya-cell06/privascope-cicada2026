"""Controlled Access: Multi-Method Authentication (Password + TOTP MFA, API Key) & RBAC."""
import hashlib
import hmac
import struct
import time
from typing import Any, Dict, Optional, Tuple


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


# Pre-provisioned Enterprise Demo Users (hashed with PBKDF2-SHA256)
USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "full_name": "Arjun Mehta (SOC Lead)",
        "role": "SOC_ADMIN",
        "salt": "salt_admin_2026",
        "password_hash": _hash_password("Admin@2026", "salt_admin_2026"),
        "totp_secret": b"PRIVASCOPE_ADMIN_TOTP_2026",
        "api_key": "pk_live_soc_admin_2026",
        "permissions": {"view", "ack_alerts", "run_scenarios", "approve_ops", "edit_settings"},
    },
    "analyst": {
        "username": "analyst",
        "full_name": "Priya Nair (Security Analyst)",
        "role": "SECURITY_ANALYST",
        "salt": "salt_analyst_2026",
        "password_hash": _hash_password("Analyst@2026", "salt_analyst_2026"),
        "totp_secret": b"PRIVASCOPE_ANALYST_TOTP_2026",
        "api_key": "pk_live_sec_analyst_2026",
        "permissions": {"view", "ack_alerts", "run_scenarios"},
    },
    "auditor": {
        "username": "auditor",
        "full_name": "Rohan Verma (Privacy Auditor)",
        "role": "PRIVACY_AUDITOR",
        "salt": "salt_auditor_2026",
        "password_hash": _hash_password("Auditor@2026", "salt_auditor_2026"),
        "totp_secret": b"PRIVASCOPE_AUDITOR_TOTP_2026",
        "api_key": "pk_live_priv_auditor_2026",
        "permissions": {"view"},
    },
}


def generate_totp(secret: bytes, time_step: int = 30, offset: int = 0) -> str:
    """RFC 6238 Time-Based One-Time Password (6-digit)."""
    counter = int(time.time() // time_step) + offset
    msg = struct.pack(">Q", counter)
    digest = hmac.new(secret, msg, hashlib.sha1).digest()
    idx = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[idx:idx + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


def verify_totp(secret: bytes, code: str) -> bool:
    code_clean = str(code).strip()
    for offset in (-1, 0, 1):
        if hmac.compare_digest(generate_totp(secret, offset=offset), code_clean):
            return True
    return False


def authenticate_password_mfa(username: str, password: str, totp_code: str) -> Tuple[Optional[Dict[str, Any]], str]:
    user = USERS_DB.get(username.strip().lower())
    if not user:
        return None, "Invalid username or password."
    expected = _hash_password(password, user["salt"])
    if not hmac.compare_digest(expected, user["password_hash"]):
        return None, "Invalid username or password."
    if not verify_totp(user["totp_secret"], totp_code):
        return None, "Invalid or expired 6-digit MFA (TOTP) code."
    return {
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "permissions": user["permissions"],
        "auth_method": "Password + TOTP MFA",
    }, "Authenticated successfully."


def authenticate_api_key(api_key: str) -> Tuple[Optional[Dict[str, Any]], str]:
    key_clean = api_key.strip()
    for user in USERS_DB.values():
        if hmac.compare_digest(user["api_key"], key_clean):
            return {
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
                "permissions": user["permissions"],
                "auth_method": "Enterprise API Key",
            }, "Authenticated via API Key."
    return None, "Invalid Enterprise API Key."


def has_permission(user: Optional[Dict[str, Any]], perm: str) -> bool:
    if not user:
        return False
    return perm in user.get("permissions", set())
