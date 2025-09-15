"""Comprehensive tests for EventQueue publish functionality."""

from __future__ import annotations

import pytest

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_red_alert_event, make_sleep_event


class TestEventQueuePublish:
    """Tests for Event publishing functionality."""

    def test_publish_single_event(self) -> None:
        """Test publishing a single event."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        assert len(q._events) == 1
        assert ev.id in q._events
        assert q._events[ev.id] is ev

    def test_publish_multiple_events(self) -> None:
        """Test publishing multiple events."""
        q = EventQueue()
        events = [
            make_sleep_event("actor1", 10),
            make_sleep_event("actor2", 20),
            make_red_alert_event("combat", False),
        ]

        for ev in events:
            q.publish(ev)

        assert len(q._events) == 3
        for ev in events:
            assert ev.id in q._events
            assert q._events[ev.id] is ev

    def test_publish_event_with_category(self) -> None:
        """Test publishing event with category indexing."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        assert "crew_admin" in q._by_category
        assert ev.id in q._by_category["crew_admin"]

    def test_publish_event_with_audience_scope(self) -> None:
        """Test publishing event with audience scope indexing."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        assert "private:actor1" in q._by_scope
        assert ev.id in q._by_scope["private:actor1"]

    def test_publish_event_with_multiple_scopes(self) -> None:
        """Test publishing event with multiple audience scopes."""
        q = EventQueue()
        ev = Event(type="MultiScopeEvent", audience_scope=["bridge", "engineering", "medical"])
        q.publish(ev)

        for scope in ["bridge", "engineering", "medical"]:
            assert scope in q._by_scope
            assert ev.id in q._by_scope[scope]

    def test_publish_event_without_category(self) -> None:
        """Test publishing event without category."""
        q = EventQueue()
        ev = Event(type="NoCategoryEvent", audience_scope=["shipwide"])
        q.publish(ev)

        assert ev.id in q._events
        assert len(q._by_category) == 0

    def test_publish_event_without_audience_scope(self) -> None:
        """Test publishing event without audience scope (should raise error)."""
        with pytest.raises(ValueError, match="Event audience_scope cannot be empty"):
            Event(type="NoScopeEvent", audience_scope=[])  # This will now raise an error

    def test_publish_duplicate_event_id(self) -> None:
        """Test publishing event with duplicate ID overwrites previous."""
        q = EventQueue()
        ev1 = Event(type="OriginalEvent", id="duplicate_id", audience_scope=["shipwide"])
        ev2 = Event(type="ReplacementEvent", id="duplicate_id", audience_scope=["shipwide"])

        q.publish(ev1)
        q.publish(ev2)

        assert len(q._events) == 1
        assert q._events["duplicate_id"] is ev2

    def test_publish_capacity_exceeded(self) -> None:
        """Test publishing when capacity is exceeded."""
        q = EventQueue(capacity=2)
        q.publish(make_sleep_event("actor1", 10))
        q.publish(make_sleep_event("actor2", 20))

        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            q.publish(make_sleep_event("actor3", 30))

    def test_publish_at_exact_capacity(self) -> None:
        """Test publishing exactly at capacity limit."""
        q = EventQueue(capacity=2)
        q.publish(make_sleep_event("actor1", 10))
        q.publish(make_sleep_event("actor2", 20))

        assert len(q._events) == 2
        assert q.capacity == 2

    def test_publish_with_empty_string_category(self) -> None:
        """Test publishing event with empty string category (not indexed)."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="", audience_scope=["shipwide"])
        q.publish(ev)

        assert ev.id in q._events
        # Empty string category is falsy, so it's not indexed
        assert "" not in q._by_category

    def test_publish_with_empty_string_scope(self) -> None:
        """Test publishing event with empty string scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=[""])
        q.publish(ev)

        assert ev.id in q._events
        assert "" in q._by_scope
        assert ev.id in q._by_scope[""]

    def test_publish_with_special_characters_in_scope(self) -> None:
        """Test publishing event with special characters in scope."""
        q = EventQueue()
        special_scopes = [
            "scope-with-dash",
            "scope_with_underscore",
            "scope.with.dots",
            "scope@domain.com",
        ]
        ev = Event(type="TestEvent", audience_scope=special_scopes)
        q.publish(ev)

        for scope in special_scopes:
            assert scope in q._by_scope
            assert ev.id in q._by_scope[scope]

    def test_publish_with_unicode_characters(self) -> None:
        """Test publishing event with unicode characters."""
        q = EventQueue()
        unicode_scope = "scope_测试_🌍"
        ev = Event(type="TestEvent", audience_scope=[unicode_scope])
        q.publish(ev)

        assert unicode_scope in q._by_scope
        assert ev.id in q._by_scope[unicode_scope]

    def test_publish_large_number_of_events(self) -> None:
        """Test publishing a large number of events."""
        q = EventQueue(capacity=1000)

        for i in range(1000):
            ev = Event(type=f"Event{i}", audience_scope=["shipwide"])
            q.publish(ev)

        assert len(q._events) == 1000

    def test_publish_events_with_same_category(self) -> None:
        """Test publishing multiple events with same category."""
        q = EventQueue()
        events = [
            Event(type="Event1", category="shared_category", audience_scope=["shipwide"]),
            Event(type="Event2", category="shared_category", audience_scope=["shipwide"]),
            Event(type="Event3", category="shared_category", audience_scope=["shipwide"]),
        ]

        for ev in events:
            q.publish(ev)

        category_events = q.list_by_category("shared_category")
        assert len(category_events) == 3
        for ev in events:
            assert ev.id in category_events

    def test_publish_events_with_same_scope(self) -> None:
        """Test publishing multiple events with same scope."""
        q = EventQueue()
        events = [
            Event(type="Event1", audience_scope=["shared_scope"]),
            Event(type="Event2", audience_scope=["shared_scope"]),
            Event(type="Event3", audience_scope=["shared_scope"]),
        ]

        for ev in events:
            q.publish(ev)

        scope_events = q.list_by_scope("shared_scope")
        assert len(scope_events) == 3
        for ev in events:
            assert ev.id in scope_events
