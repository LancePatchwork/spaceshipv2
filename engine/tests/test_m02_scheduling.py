from __future__ import annotations

from engine.m02_events.models import Event
from engine.m02_events.queue import EventQueue
from engine.m02_events.scheduling import check_claim_ttl, effective_priority
from engine.m02_events.subscriptions import SubscriptionBroker


def test_preemption_suspends_active_event() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    broker.subscribe("alice", "private:alice", "shipwide")
    sleep = Event(type="crew.sleep", priority=50, audience_scope=["private:alice"])
    eq.publish(sleep)
    broker.on_publish(sleep, save_seed=1)
    claimed = broker.claim("alice")
    assert claimed is not None
    broker.mark_active("alice", claimed.id)

    alert = Event(
        type="alerts.red",
        priority=0,
        preemptible=False,
        audience_scope=["shipwide"],
    )
    eq.publish(alert)
    broker.on_publish(alert, save_seed=1)

    refreshed = eq.get_by_id(claimed.id)
    assert refreshed is not None and refreshed.state == "suspended"
    first = broker.peek("alice")
    assert first is not None and first.id == alert.id
    claimed_alert = broker.claim("alice")
    assert claimed_alert is not None and claimed_alert.id == alert.id
    next_peek = broker.peek("alice")
    assert next_peek is not None and next_peek.id == claimed.id


def test_effective_priority_aging_bounds() -> None:
    now_ms = 1_000_000
    e = Event(type="task", priority=40, ts_ms=now_ms - 130_000, audience_scope=["shipwide"])
    assert effective_priority(e, now_ms) == 36
    e2 = Event(type="task", priority=40, ts_ms=now_ms - 2_000_000, audience_scope=["shipwide"])
    assert effective_priority(e2, now_ms) == 5
    e3 = Event(type="task", priority=0, ts_ms=now_ms - 2_000_000, audience_scope=["shipwide"])
    assert effective_priority(e3, now_ms) == 0


def test_effective_priority_no_aging() -> None:
    """Test effective priority when wait time is within aging threshold (line 39)."""
    now_ms = 1_000_000
    # Create event with wait time less than AGING_S (60 seconds)
    e = Event(
        type="task", priority=40, ts_ms=now_ms - 30_000, audience_scope=["shipwide"]
    )  # 30 seconds ago
    assert effective_priority(e, now_ms) == 40  # Should return original priority (line 39)


def test_claim_ttl_skips_non_claimed_events() -> None:
    """Test that check_claim_ttl skips events that are not claimed or have progress (line 61)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    broker.subscribe("alice", "private:alice")

    # Create an event that's not claimed
    e1 = Event(type="crew.sleep", priority=50, audience_scope=["private:alice"])
    eq.publish(e1)
    broker.on_publish(e1, save_seed=1)

    # Create an event that's claimed but has progress
    e2 = Event(type="crew.sleep", priority=50, audience_scope=["private:alice"])
    eq.publish(e2)
    broker.on_publish(e2, save_seed=1)
    claimed = broker.claim("alice")
    assert claimed is not None
    broker.mark_active("alice", claimed.id)
    # Simulate progress
    claimed.progress = 0.5
    eq.update(claimed)

    # check_claim_ttl should skip both events (line 61)
    expired = check_claim_ttl(broker, 1_000_000, claim_ttl_s=1, save_seed=1)
    assert len(expired) == 0


def test_claim_ttl_returns_event_and_escalates() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    broker.subscribe("alice", "private:alice")
    e = Event(type="crew.sleep", priority=50, audience_scope=["private:alice"])
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim("alice")
    assert claimed is not None
    claim_ts = claimed.audit[-1]["ts"]
    now_ms = claim_ts + 2_000

    expired = check_claim_ttl(broker, now_ms, claim_ttl_s=1, save_seed=1)
    assert claimed.id in expired
    refreshed = eq.get_by_id(claimed.id)
    assert refreshed is not None
    assert refreshed.state == "queued"
    assert refreshed.taker is None
    assert "officers" in refreshed.audience_scope
    peeked = broker.peek("alice")
    assert peeked is not None and peeked.id == claimed.id
