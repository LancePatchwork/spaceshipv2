from __future__ import annotations

import heapq

import pytest

from engine.lib.rng import seed_for
from engine.m02_events import EventQueue
from engine.m02_events.factories import (
    make_red_alert_event,
    make_repair_event,
    make_sleep_event,
)
from engine.m02_events.subscriptions import SubscriptionBroker


def test_subscribed_actor_receives_events() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    broker.subscribe("a1", "shipwide", "department:engineering")
    e = make_repair_event("s1", severity="minor")
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    assert broker.peek("a1") is e
    assert broker.peek("a2") is None


def test_claim_selects_highest_priority() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    broker.subscribe("a1", "department:engineering")
    e_low = make_repair_event("s1", severity="minor")
    e_high = make_repair_event("s2", severity="critical")
    eq.publish(e_low)
    eq.publish(e_high)
    broker.on_publish(e_low, save_seed=1)
    broker.on_publish(e_high, save_seed=1)
    first = broker.claim("a1")
    assert first is not None and first.id == e_high.id
    second = broker.claim("a1")
    assert second is not None and second.id == e_low.id


def test_tie_break_is_deterministic() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")
    e1 = make_red_alert_event("combat", False)
    e2 = make_red_alert_event("collision", False)
    eq.publish(e1)
    eq.publish(e2)
    seed = 42
    broker.on_publish(e1, seed)
    broker.on_publish(e2, seed)
    r1 = seed_for(seed, actor, e1.id).random()
    r2 = seed_for(seed, actor, e2.id).random()
    expected_first = e1 if r1 < r2 else e2
    first = broker.claim(actor)
    assert first is not None and first.id == expected_first.id
    second = broker.claim(actor)
    assert second is not None and {first.id, second.id} == {e1.id, e2.id}


def test_state_transitions() -> None:
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, f"private:{actor}")
    e = make_sleep_event(actor, 5)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None and claimed.state == "claimed"
    broker.mark_active(actor, claimed.id)
    ev = eq.get_by_id(claimed.id)
    assert ev is not None and ev.state == "active"
    broker.suspend(actor, claimed.id)
    ev = eq.get_by_id(claimed.id)
    assert ev is not None and ev.state == "suspended"
    broker.mark_active(actor, claimed.id)
    ev = eq.get_by_id(claimed.id)
    assert ev is not None and ev.state == "active"
    broker.done(actor, claimed.id)
    ev = eq.get_by_id(claimed.id)
    assert ev is not None and ev.state == "done"


def test_unsubscribe() -> None:
    """Test unsubscribe functionality (lines 25-29)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide", "department:engineering")

    # Unsubscribe from one scope
    broker.unsubscribe(actor, "department:engineering")

    # Should still receive shipwide events
    e1 = make_red_alert_event("combat", False)
    eq.publish(e1)
    broker.on_publish(e1, save_seed=1)
    assert broker.peek(actor) is e1

    # Should not receive department events
    e2 = make_repair_event("s1", severity="minor")
    eq.publish(e2)
    broker.on_publish(e2, save_seed=1)
    # Clear the shipwide event first
    broker.claim(actor)
    assert broker.peek(actor) is None  # No department events


def test_unsubscribe_nonexistent_actor() -> None:
    """Test unsubscribe with nonexistent actor (lines 25-27)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    # Should not raise an error
    broker.unsubscribe("nonexistent", "shipwide")


def test_next_event_id_empty_heap() -> None:
    """Test _next_event_id with empty heap (lines 58-59)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # No events published, so heap should be empty
    assert broker.peek(actor) is None


def test_next_event_id_stale_references() -> None:
    """Test _next_event_id with stale event references (lines 63-65, 71)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish an event
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)

    # Remove the event directly from the queue (simulating external deletion)
    del eq._events[e.id]

    # The broker should handle the stale reference gracefully
    assert broker.peek(actor) is None


def test_next_event_id_suspended_event() -> None:
    """Test _next_event_id with suspended event (lines 68-69)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide", "department:engineering")

    # Create a low priority event and make it active
    e1 = make_repair_event("s1", severity="minor")  # priority 40
    eq.publish(e1)
    broker.on_publish(e1, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None
    broker.mark_active(actor, claimed.id)

    # Create a high priority event that will preempt the first one
    e2 = make_red_alert_event("combat", False)  # priority 0
    eq.publish(e2)
    broker.on_publish(e2, save_seed=1)

    # The first event should now be suspended and in the heap
    # We should be able to peek at the suspended event
    peeked = broker.peek(actor)
    assert peeked is not None and peeked.id == e2.id  # The higher priority event should be first

    # But the suspended event should still be in the heap
    # Let's claim the high priority event and then check for the suspended one
    broker.claim(actor)
    peeked = broker.peek(actor)
    assert peeked is not None and peeked.id == claimed.id  # Should be the suspended event


def test_next_event_id_remove_stale_references() -> None:
    """Test _next_event_id removes stale references (line 71)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish an event and claim it
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None

    # Mark as done (this should remove it from the heap)
    broker.done(actor, claimed.id)

    # Should not be able to peek at the done event
    assert broker.peek(actor) is None


def test_preemption_logic() -> None:
    """Test preemption logic in on_publish (lines 37-39)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide", "department:engineering")

    # Create a low priority event and make it active
    e1 = make_repair_event("s1", severity="minor")  # priority 40
    eq.publish(e1)
    broker.on_publish(e1, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None
    broker.mark_active(actor, claimed.id)

    # Create a high priority event that should preempt
    e2 = make_red_alert_event("combat", False)  # priority 0
    eq.publish(e2)
    broker.on_publish(e2, save_seed=1)

    # The original event should be suspended
    refreshed = eq.get_by_id(claimed.id)
    assert refreshed is not None and refreshed.state == "suspended"

    # The new event should be available
    peeked = broker.peek(actor)
    assert peeked is not None and peeked.id == e2.id


def test_audience_scope_matching() -> None:
    """Test audience scope matching logic (line 33)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "department:engineering")

    # Event with matching scope should be received
    e1 = make_repair_event("s1", severity="minor")
    eq.publish(e1)
    broker.on_publish(e1, save_seed=1)
    assert broker.peek(actor) is e1

    # Clear the event
    broker.claim(actor)

    # Event with non-matching scope should not be received
    e2 = make_sleep_event("other_actor", 5)
    eq.publish(e2)
    broker.on_publish(e2, save_seed=1)
    assert broker.peek(actor) is None


def test_shipwide_events_always_received() -> None:
    """Test that shipwide events are always received regardless of subscriptions (line 33)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "department:engineering")  # Only subscribe to engineering

    # Shipwide event should be received even though actor only subscribes to engineering
    e = make_red_alert_event("combat", False)  # This has shipwide audience_scope
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    assert broker.peek(actor) is e


def test_claim_empty_heap() -> None:
    """Test claim with empty heap to cover line 83."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # No events published, so claim should return None
    result = broker.claim(actor)
    assert result is None


def test_claim_skips_non_queued_events() -> None:
    """Test claim skips non-queued events to cover line 88."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish an event and claim it
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None

    # Mark as active
    broker.mark_active(actor, claimed.id)

    # Try to claim again - should skip the active event and return None
    result = broker.claim(actor)
    assert result is None


def test_claim_returns_none_when_no_valid_events() -> None:
    """Test claim returns None when no valid events to cover line 94."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish an event and claim it
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None

    # Mark as done
    broker.done(actor, claimed.id)

    # Try to claim again - should return None
    result = broker.claim(actor)
    assert result is None


def test_mark_active_invalid_event() -> None:
    """Test mark_active with invalid event to cover line 99."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"

    # Try to mark non-existent event as active
    with pytest.raises(KeyError):
        broker.mark_active(actor, "nonexistent_id")


def test_mark_active_invalid_state() -> None:
    """Test mark_active with invalid state to cover line 101."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish and claim an event
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None

    # Mark as active first
    broker.mark_active(actor, claimed.id)

    # Try to mark as active again - should raise ValueError
    with pytest.raises(ValueError, match="invalid state"):
        broker.mark_active(actor, claimed.id)


def test_done_invalid_event() -> None:
    """Test done with invalid event to cover line 109."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"

    # Try to mark non-existent event as done
    with pytest.raises(KeyError):
        broker.done(actor, "nonexistent_id")


def test_suspend_invalid_event() -> None:
    """Test suspend with invalid event to cover line 117."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"

    # Try to suspend non-existent event
    with pytest.raises(KeyError):
        broker.suspend(actor, "nonexistent_id")


def test_suspend_invalid_state() -> None:
    """Test suspend with invalid state to cover line 119."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish and claim an event
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)
    claimed = broker.claim(actor)
    assert claimed is not None

    # Try to suspend a claimed (not active) event - should raise ValueError
    with pytest.raises(ValueError, match="invalid state"):
        broker.suspend(actor, claimed.id)


def test_next_event_id_remove_stale_references_duplicate() -> None:
    """Test _next_event_id removes stale references to cover line 71 (duplicate)."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide")

    # Publish an event
    e = make_red_alert_event("combat", False)
    eq.publish(e)
    broker.on_publish(e, save_seed=1)

    # Manually add a stale reference to the heap
    heap = broker._personal.setdefault(actor, [])
    heapq.heappush(heap, (0, 0, 0, "stale_id"))

    # The _next_event_id should remove the stale reference
    event_id = broker._next_event_id(actor)
    assert event_id == e.id  # Should return the valid event, not the stale one


def test_claim_skips_all_non_queued_events() -> None:
    """Test claim skips all non-queued events and returns None to cover lines 88, 94."""
    eq = EventQueue()
    broker = SubscriptionBroker(eq)
    actor = "a1"
    broker.subscribe(actor, "shipwide", "department:engineering")

    # Publish multiple events
    e1 = make_red_alert_event("combat", False)
    e2 = make_repair_event("s1", severity="minor")
    eq.publish(e1)
    eq.publish(e2)
    broker.on_publish(e1, save_seed=1)
    broker.on_publish(e2, save_seed=1)

    # Claim and mark first event as active
    claimed1 = broker.claim(actor)
    assert claimed1 is not None
    broker.mark_active(actor, claimed1.id)

    # Claim and mark second event as done
    claimed2 = broker.claim(actor)
    assert claimed2 is not None
    broker.done(actor, claimed2.id)

    # Now try to claim again - should skip both non-queued events and return None
    result = broker.claim(actor)
    assert result is None
