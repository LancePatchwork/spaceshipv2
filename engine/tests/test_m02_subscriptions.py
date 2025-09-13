from __future__ import annotations

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
