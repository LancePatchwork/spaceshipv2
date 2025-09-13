from __future__ import annotations

import math
from typing import TYPE_CHECKING, List

from engine.m02_events.models import Event

if TYPE_CHECKING:  # pragma: no cover
    from engine.m02_events.subscriptions import SubscriptionBroker

AGING_S = 120
STEP_S = 30
MIN_PRIORITY = 5


def should_preempt(current: Event, incoming: Event) -> bool:
    """Return True if *incoming* should preempt *current*.

    Preemption occurs when the incoming event has a strictly higher priority
    (numerically lower) than the current event and the current event is
    marked as preemptible.
    """

    return incoming.priority < current.priority and current.preemptible


def effective_priority(e: Event, now_ms: int) -> int:
    """Return the priority adjusted for aging.

    Non‑critical events (priority > 0) age over time. After AGING_S seconds,
    the priority is lowered (numerically) by ``floor(wait_s / STEP_S)`` but
    never below ``MIN_PRIORITY``.
    """

    if e.priority == 0:
        return 0
    wait_s = max(0, (now_ms - e.ts_ms) // 1000)
    if wait_s <= AGING_S:
        return e.priority
    aged = e.priority - math.floor(wait_s / STEP_S)
    return max(MIN_PRIORITY, aged)


def check_claim_ttl(
    broker: "SubscriptionBroker",
    now_ms: int,
    *,
    claim_ttl_s: int = 120,
    save_seed: int = 0,
) -> List[str]:
    """Expire stale claims and return affected event IDs.

    Events in ``claimed`` state with no progress for ``claim_ttl_s`` seconds
    are returned to the queue, their taker cleared, and ``officers`` added to
    the audience_scope if not already present.
    """

    expired: List[str] = []
    for e in list(broker._eq._events.values()):  # internal iteration
        if e.state != "claimed" or e.progress > 0:
            continue
        claim_ts = 0
        for entry in reversed(e.audit):
            if entry.get("action") == "claim":
                claim_ts = int(entry.get("ts", 0))
                break
        if claim_ts and now_ms - claim_ts > claim_ttl_s * 1000:
            e.state = "queued"
            e.taker = None
            if "officers" not in e.audience_scope:
                e.audience_scope.append("officers")
            e.append_audit("system", "claim_timeout")
            broker._eq.update(e)
            broker.on_publish(e, save_seed)
            expired.append(e.id)
    return expired


__all__ = [
    "AGING_S",
    "STEP_S",
    "MIN_PRIORITY",
    "should_preempt",
    "effective_priority",
    "check_claim_ttl",
]
