from __future__ import annotations

import pytest

from engine.m02_events.factories import (
    make_red_alert_event,
    make_repair_event,
    make_sleep_event,
)


def test_red_alert_defaults() -> None:
    ev = make_red_alert_event("combat", True)
    assert ev.priority == 0
    assert ev.category == "alerts"
    assert ev.audience_scope == ["shipwide"]
    assert ev.payload == {"reason": "combat", "auto_stations": True}


def test_sleep_factory() -> None:
    ev = make_sleep_event("crew1", 5)
    assert ev.priority == 90
    assert ev.category == "crew_admin"
    assert ev.audience_scope == ["private:crew1"]
    assert ev.payload["duration_s"] == 5
    with pytest.raises(ValueError):
        make_sleep_event("crew1", -1)


def test_repair_factory() -> None:
    ev = make_repair_event("sys42", severity="critical")
    assert ev.priority == 5
    assert ev.category == "engineering"
    assert ev.audience_scope == ["department:engineering", "officers"]
    assert ev.payload["system_id"] == "sys42"
    assert ev.payload["severity"] == "critical"
    assert "location" not in ev.payload  # No location provided


def test_repair_factory_with_location() -> None:
    """Test repair factory with location parameter to cover line 43."""
    ev = make_repair_event("sys42", location="deck_3", severity="minor")
    assert ev.priority == 40
    assert ev.category == "engineering"
    assert ev.audience_scope == ["department:engineering", "officers"]
    assert ev.payload["system_id"] == "sys42"
    assert ev.payload["severity"] == "minor"
    assert ev.payload["location"] == "deck_3"  # Location should be included


def test_sleep_factory_negative_duration() -> None:
    """Test sleep factory with negative duration to cover lines 23-25."""
    with pytest.raises(ValueError, match="duration_s must be non-negative"):
        make_sleep_event("actor1", -5)
