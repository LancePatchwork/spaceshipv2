from __future__ import annotations

from datetime import datetime, timezone


def utc_ms_now() -> int:
    """Return the current UTC time in milliseconds since the epoch."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


__all__ = ["utc_ms_now", "now_iso"]
