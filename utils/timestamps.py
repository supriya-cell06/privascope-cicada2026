"""UTC and event-time timestamp utilities."""
from datetime import datetime, timezone, timedelta


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts: str) -> datetime:
    if not ts:
        return utc_now()
    ts_clean = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts_clean)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def seconds_since(ts: str) -> float:
    return max(0.0, (utc_now() - parse_iso(ts)).total_seconds())


def iso_offset(seconds_delta: float) -> str:
    dt = utc_now() + timedelta(seconds=seconds_delta)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
