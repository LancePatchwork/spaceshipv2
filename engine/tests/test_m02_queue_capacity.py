"""Comprehensive tests for EventQueue capacity management."""

from __future__ import annotations

import pytest

from engine.m02_events import EventQueue
from engine.m02_events.factories import make_red_alert_event, make_sleep_event


class TestEventQueueCapacity:
    """Tests for EventQueue capacity management."""

    def test_capacity_limit(self) -> None:
        """Test basic capacity limit enforcement."""
        q = EventQueue(capacity=1)
        q.publish(make_red_alert_event("combat", False))
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(make_sleep_event("b", 5))

    def test_capacity_zero(self) -> None:
        """Test queue with zero capacity."""
        q = EventQueue(capacity=0)
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(make_sleep_event("actor1", 10))

    def test_capacity_large_number(self) -> None:
        """Test queue with very large capacity."""
        q = EventQueue(capacity=100_000)
        # Should be able to publish many events
        for i in range(1000):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        assert len(q._events) == 1000

    def test_capacity_after_update(self) -> None:
        """Test that updates don't affect capacity."""
        q = EventQueue(capacity=2)
        ev1 = make_sleep_event("actor1", 10)
        ev2 = make_sleep_event("actor2", 20)

        q.publish(ev1)
        q.publish(ev2)

        # Update should not affect capacity
        updated_ev1 = ev1.model_copy(update={"priority": 75})
        q.update(updated_ev1)

        # Should still be at capacity
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(make_sleep_event("actor3", 30))

    def test_capacity_with_duplicate_ids(self) -> None:
        """Test capacity behavior with duplicate event IDs."""
        q = EventQueue(capacity=2)

        # Publish first event
        ev1 = make_sleep_event("actor1", 10)
        q.publish(ev1)

        # Publish second event
        ev2 = make_sleep_event("actor2", 20)
        q.publish(ev2)

        # Now we're at capacity, publishing with duplicate ID should fail
        # because capacity check happens before duplicate check
        ev1_duplicate = make_sleep_event("actor1", 15)  # Same actor, different duration
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(ev1_duplicate)

        assert len(q._events) == 2  # Still only 2 unique events

    def test_capacity_negative(self) -> None:
        """Test queue with negative capacity."""
        q = EventQueue(capacity=-1)
        # Negative capacity means len(self._events) >= -1 is always true
        # So capacity check should always fail
        ev = make_sleep_event("actor1", 10)
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(ev)

    def test_capacity_one(self) -> None:
        """Test queue with capacity of one."""
        q = EventQueue(capacity=1)
        ev1 = make_sleep_event("actor1", 10)
        q.publish(ev1)

        # Should be at capacity now
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev2 = make_sleep_event("actor2", 20)
            q.publish(ev2)

    def test_capacity_exact_limit(self) -> None:
        """Test publishing exactly at capacity limit."""
        q = EventQueue(capacity=5)

        # Publish exactly 5 events
        for i in range(5):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        assert len(q._events) == 5

        # Next event should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev = make_sleep_event("actor5", 10)
            q.publish(ev)

    def test_capacity_with_different_event_types(self) -> None:
        """Test capacity with different types of events."""
        q = EventQueue(capacity=3)

        # Mix of different event types
        ev1 = make_sleep_event("actor1", 10)
        ev2 = make_red_alert_event("combat", False)
        ev3 = make_sleep_event("actor2", 20)

        q.publish(ev1)
        q.publish(ev2)
        q.publish(ev3)

        assert len(q._events) == 3

        # Next event should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev4 = make_red_alert_event("medical", True)
            q.publish(ev4)

    def test_capacity_error_message(self) -> None:
        """Test that capacity exceeded error has correct message."""
        q = EventQueue(capacity=1)
        ev1 = make_sleep_event("actor1", 10)
        q.publish(ev1)

        with pytest.raises(RuntimeError) as exc_info:
            ev2 = make_sleep_event("actor2", 20)
            q.publish(ev2)

        assert "queue capacity exceeded" in str(exc_info.value)

    def test_capacity_with_updates(self) -> None:
        """Test capacity behavior when events are updated."""
        q = EventQueue(capacity=2)

        ev1 = make_sleep_event("actor1", 10)
        ev2 = make_sleep_event("actor2", 20)

        q.publish(ev1)
        q.publish(ev2)

        # Update an event - should not affect capacity
        updated_ev1 = ev1.model_copy(update={"priority": 75})
        q.update(updated_ev1)

        # Should still be at capacity
        assert len(q._events) == 2

        # Try to publish another event - should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev3 = make_sleep_event("actor3", 30)
            q.publish(ev3)

    def test_capacity_very_small(self) -> None:
        """Test queue with very small capacity."""
        q = EventQueue(capacity=1)
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        # Should be at capacity
        assert len(q._events) == 1

        # Any additional publish should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev2 = make_sleep_event("actor2", 20)
            q.publish(ev2)

    def test_capacity_large_but_limited(self) -> None:
        """Test queue with large but still limited capacity."""
        q = EventQueue(capacity=100)

        # Publish up to capacity
        for i in range(100):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        assert len(q._events) == 100

        # Next event should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev = make_sleep_event("actor100", 10)
            q.publish(ev)

    def test_capacity_with_mixed_operations(self) -> None:
        """Test capacity with mixed publish and update operations."""
        q = EventQueue(capacity=3)

        # Publish two events
        ev1 = make_sleep_event("actor1", 10)
        ev2 = make_sleep_event("actor2", 20)
        q.publish(ev1)
        q.publish(ev2)

        # Update one event
        updated_ev1 = ev1.model_copy(update={"priority": 75})
        q.update(updated_ev1)

        # Publish third event
        ev3 = make_sleep_event("actor3", 30)
        q.publish(ev3)

        assert len(q._events) == 3

        # Fourth event should fail
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            ev4 = make_sleep_event("actor4", 40)
            q.publish(ev4)
