from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from engine.m02_events import Event


def test_event_autofills_id_and_ts() -> None:
    ev = Event(type="TestEvent")
    assert len(ev.id) == 26
    assert isinstance(ev.ts_ms, int)


def test_priority_validation() -> None:
    with pytest.raises(ValidationError):
        Event(type="TestEvent", priority=-1)


def test_append_audit() -> None:
    ev = Event(type="TestEvent")
    ev.append_audit("actor1", "claimed", {"k": "v"})
    assert len(ev.audit) == 1
    entry = ev.audit[0]
    assert entry["actor_id"] == "actor1"
    assert isinstance(entry["ts"], int)
    # verify timestamp parses
    datetime.fromtimestamp(entry["ts"] / 1000)
