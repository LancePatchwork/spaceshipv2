from __future__ import annotations

import os
import time
import warnings
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from engine.lib.timeutil import utc_ms_now

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid() -> str:
    """Return a new ULID string."""
    timestamp_ms = int(time.time() * 1000)
    time_bytes = timestamp_ms.to_bytes(6, "big")
    random_bytes = os.urandom(10)
    value = int.from_bytes(time_bytes + random_bytes, "big")
    chars = []
    for _ in range(26):
        chars.append(_ULID_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


class Event(BaseModel):
    id: str = Field(default_factory=new_ulid)
    type: str
    ts_ms: int = Field(default_factory=utc_ms_now)
    issuer: str | None = None
    audience_scope: list[str] = Field(default_factory=list)
    category: str | None = None
    priority: int = 50
    max_request_priority: int | None = None
    preemptible: bool = True
    deadline: datetime | None = None
    ttl_seconds: int | None = None
    dependencies: list[str] = Field(default_factory=list)
    state: Literal[
        "queued",
        "routed",
        "claimed",
        "active",
        "suspended",
        "done",
        "failed",
        "expired",
        "cancelled",
    ] = "queued"
    taker: str | None = None
    team_size: int = 1
    parent_id: str | None = None
    group_id: str | None = None
    idempotency_key: str | None = None
    progress: float = 0.0
    eta_s: int | None = None
    severity: Literal["info", "warn", "critical"] | None = None
    qualifiers: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    payload: dict[str, object] = Field(default_factory=dict)
    audit: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("priority must be between 0 and 100")
        return v

    @field_validator("progress")
    @classmethod
    def _validate_progress(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("progress must be between 0 and 1")
        return v

    @field_validator("audience_scope")
    @classmethod
    def _warn_empty_audience(cls, v: list[str]) -> list[str]:
        if not v:
            warnings.warn("Event audience_scope is empty")
        return v

    def append_audit(
        self, actor_id: str, action: str, details: dict[str, object] | None = None
    ) -> None:
        self.audit.append(
            {
                "ts": utc_ms_now(),
                "actor_id": actor_id,
                "action": action,
                "details": details or {},
            }
        )


__all__ = ["Event", "new_ulid"]
