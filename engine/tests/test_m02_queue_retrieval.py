"""Comprehensive tests for EventQueue retrieval functionality."""

from __future__ import annotations

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_sleep_event


class TestEventQueueRetrieval:
    """Tests for Event retrieval functionality."""

    def test_get_by_id_existing(self) -> None:
        """Test getting existing event by ID."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved is ev

    def test_get_by_id_nonexistent(self) -> None:
        """Test getting non-existent event by ID returns None."""
        q = EventQueue()
        retrieved = q.get_by_id("nonexistent_id")
        assert retrieved is None

    def test_get_by_id_empty_queue(self) -> None:
        """Test getting event by ID from empty queue."""
        q = EventQueue()
        retrieved = q.get_by_id("any_id")
        assert retrieved is None

    def test_list_by_category_existing(self) -> None:
        """Test listing events by existing category."""
        q = EventQueue()
        ev1 = Event(type="Event1", category="test_category", audience_scope=["shipwide"])
        ev2 = Event(type="Event2", category="test_category", audience_scope=["shipwide"])
        ev3 = Event(type="Event3", category="other_category", audience_scope=["shipwide"])

        q.publish(ev1)
        q.publish(ev2)
        q.publish(ev3)

        events = q.list_by_category("test_category")
        assert len(events) == 2
        assert ev1.id in events
        assert ev2.id in events
        assert ev3.id not in events

    def test_list_by_category_nonexistent(self) -> None:
        """Test listing events by non-existent category."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="existing_category", audience_scope=["shipwide"])
        q.publish(ev)

        events = q.list_by_category("nonexistent_category")
        assert events == []

    def test_list_by_category_empty_queue(self) -> None:
        """Test listing events by category from empty queue."""
        q = EventQueue()
        events = q.list_by_category("any_category")
        assert events == []

    def test_list_by_scope_existing(self) -> None:
        """Test listing events by existing scope."""
        q = EventQueue()
        ev1 = Event(type="Event1", audience_scope=["test_scope"])
        ev2 = Event(type="Event2", audience_scope=["test_scope"])
        ev3 = Event(type="Event3", audience_scope=["other_scope"])

        q.publish(ev1)
        q.publish(ev2)
        q.publish(ev3)

        events = q.list_by_scope("test_scope")
        assert len(events) == 2
        assert ev1.id in events
        assert ev2.id in events
        assert ev3.id not in events

    def test_list_by_scope_nonexistent(self) -> None:
        """Test listing events by non-existent scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["existing_scope"])
        q.publish(ev)

        events = q.list_by_scope("nonexistent_scope")
        assert events == []

    def test_list_by_scope_empty_queue(self) -> None:
        """Test listing events by scope from empty queue."""
        q = EventQueue()
        events = q.list_by_scope("any_scope")
        assert events == []

    def test_list_by_scope_multiple_scopes(self) -> None:
        """Test listing events when event has multiple scopes."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["scope1", "scope2"])
        q.publish(ev)

        events_scope1 = q.list_by_scope("scope1")
        events_scope2 = q.list_by_scope("scope2")

        assert events_scope1 == [ev.id]
        assert events_scope2 == [ev.id]

    def test_retrieval_returns_copies(self) -> None:
        """Test that retrieval methods return copies of lists."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="test_category", audience_scope=["test_scope"])
        q.publish(ev)

        category_list1 = q.list_by_category("test_category")
        category_list2 = q.list_by_category("test_category")
        scope_list1 = q.list_by_scope("test_scope")
        scope_list2 = q.list_by_scope("test_scope")

        # Lists should be equal but not the same object
        assert category_list1 == category_list2
        assert category_list1 is not category_list2
        assert scope_list1 == scope_list2
        assert scope_list1 is not scope_list2

    def test_retrieval_with_empty_strings(self) -> None:
        """Test retrieval with empty string category and scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="", audience_scope=[""])
        q.publish(ev)

        category_events = q.list_by_category("")
        scope_events = q.list_by_scope("")

        # Empty string category is falsy, so it's not indexed
        assert category_events == []
        assert scope_events == [ev.id]

    def test_retrieval_with_special_characters(self) -> None:
        """Test retrieval with special characters in category and scope."""
        q = EventQueue()
        special_category = "category-with-dashes"
        special_scope = "scope_with_underscores"

        ev = Event(type="TestEvent", category=special_category, audience_scope=[special_scope])
        q.publish(ev)

        category_events = q.list_by_category(special_category)
        scope_events = q.list_by_scope(special_scope)

        assert category_events == [ev.id]
        assert scope_events == [ev.id]

    def test_retrieval_with_unicode(self) -> None:
        """Test retrieval with unicode characters."""
        q = EventQueue()
        unicode_category = "category_测试"
        unicode_scope = "scope_🌍"

        ev = Event(type="TestEvent", category=unicode_category, audience_scope=[unicode_scope])
        q.publish(ev)

        category_events = q.list_by_category(unicode_category)
        scope_events = q.list_by_scope(unicode_scope)

        assert category_events == [ev.id]
        assert scope_events == [ev.id]

    def test_retrieval_after_update(self) -> None:
        """Test retrieval after event updates."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="old_category", audience_scope=["old_scope"])
        q.publish(ev)

        # Verify initial retrieval
        assert q.list_by_category("old_category") == [ev.id]
        assert q.list_by_scope("old_scope") == [ev.id]

        # Update event
        updated_ev = ev.model_copy(
            update={"category": "new_category", "audience_scope": ["new_scope"]}
        )
        q.update(updated_ev)

        # Verify updated retrieval
        assert q.list_by_category("old_category") == []
        assert q.list_by_scope("old_scope") == []
        assert q.list_by_category("new_category") == [ev.id]
        assert q.list_by_scope("new_scope") == [ev.id]

    def test_retrieval_with_large_dataset(self) -> None:
        """Test retrieval performance with large dataset."""
        q = EventQueue(capacity=1000)

        # Create events with various categories and scopes
        categories = ["cat1", "cat2", "cat3"]
        scopes = ["scope1", "scope2", "scope3"]

        for i in range(100):
            category = categories[i % len(categories)]
            scope = scopes[i % len(scopes)]
            ev = Event(type=f"Event{i}", category=category, audience_scope=[scope])
            q.publish(ev)

        # Test retrieval
        for category in categories:
            events = q.list_by_category(category)
            # 100 events distributed across 3 categories: 33, 33, 34
            assert len(events) in [33, 34]  # Allow for uneven distribution

        for scope in scopes:
            events = q.list_by_scope(scope)
            # 100 events distributed across 3 scopes: 33, 33, 34
            assert len(events) in [33, 34]  # Allow for uneven distribution

    def test_retrieval_consistency(self) -> None:
        """Test that retrieval results are consistent."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="test_category", audience_scope=["test_scope"])
        q.publish(ev)

        # Multiple retrievals should return same results
        for _ in range(10):
            assert q.get_by_id(ev.id) is ev
            assert q.list_by_category("test_category") == [ev.id]
            assert q.list_by_scope("test_scope") == [ev.id]
