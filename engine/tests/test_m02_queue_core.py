from __future__ import annotations

import pytest

from engine.m02_events import EventQueue
from engine.m02_events.factories import make_red_alert_event, make_sleep_event


def test_publish_indexes() -> None:
    q = EventQueue()
    ev = make_sleep_event("a1", 10)
    q.publish(ev)
    assert q.get_by_id(ev.id) is ev
    assert q.list_by_category("crew_admin") == [ev.id]
    assert q.list_by_scope("private:a1") == [ev.id]


def test_update_reindexes() -> None:
    q = EventQueue()
    ev = make_sleep_event("a1", 10)
    q.publish(ev)
    updated = ev.model_copy(update={"audience_scope": ["officers"], "category": "crew_admin"})
    q.update(updated)
    assert q.list_by_scope("private:a1") == []
    assert q.list_by_scope("officers") == [ev.id]


def test_capacity_limit() -> None:
    q = EventQueue(capacity=1)
    q.publish(make_red_alert_event("combat", False))
    with pytest.raises(RuntimeError):
        q.publish(make_sleep_event("b", 5))
