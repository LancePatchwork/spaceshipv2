"""Comprehensive tests for EventQueue update functionality."""

from __future__ import annotations

import pytest

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_sleep_event


class TestEventQueueUpdate:
    """Tests for Event update functionality."""

    def test_update_existing_event(self) -> None:
        """Test updating an existing event."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        updated_ev = ev.model_copy(update={"priority": 75, "state": "active"})
        q.update(updated_ev)

        stored_ev = q.get_by_id(ev.id)
        assert stored_ev.priority == 75
        assert stored_ev.state == "active"
        assert len(stored_ev.audit) == 1
        assert stored_ev.audit[0]["action"] == "update"

    def test_update_nonexistent_event(self) -> None:
        """Test updating a non-existent event raises KeyError."""
        q = EventQueue()
        ev = Event(type="NonExistentEvent", id="nonexistent_id", audience_scope=["shipwide"])

        with pytest.raises(KeyError, match="event nonexistent_id not found"):
            q.update(ev)

    def test_update_category_change(self) -> None:
        """Test updating event with category change."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="old_category", audience_scope=["shipwide"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"category": "new_category"})
        q.update(updated_ev)

        assert q.list_by_category("old_category") == []
        assert q.list_by_category("new_category") == [ev.id]

    def test_update_category_removal(self) -> None:
        """Test updating event to remove category."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="test_category", audience_scope=["shipwide"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"category": None})
        q.update(updated_ev)

        assert q.list_by_category("test_category") == []
        assert updated_ev.category is None

    def test_update_category_addition(self) -> None:
        """Test updating event to add category."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"category": "new_category"})
        q.update(updated_ev)

        assert q.list_by_category("new_category") == [ev.id]

    def test_update_audience_scope_change(self) -> None:
        """Test updating event with audience scope change."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["old_scope"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"audience_scope": ["new_scope"]})
        q.update(updated_ev)

        assert q.list_by_scope("old_scope") == []
        assert q.list_by_scope("new_scope") == [ev.id]

    def test_update_audience_scope_removal(self) -> None:
        """Test updating event to remove audience scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["test_scope"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"audience_scope": []})
        q.update(updated_ev)

        assert q.list_by_scope("test_scope") == []
        assert updated_ev.audience_scope == []

    def test_update_audience_scope_addition(self) -> None:
        """Test updating event to add audience scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"audience_scope": ["new_scope"]})
        q.update(updated_ev)

        assert q.list_by_scope("new_scope") == [ev.id]

    def test_update_multiple_scopes_change(self) -> None:
        """Test updating event with multiple scope changes."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["scope1", "scope2"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"audience_scope": ["scope3", "scope4"]})
        q.update(updated_ev)

        assert q.list_by_scope("scope1") == []
        assert q.list_by_scope("scope2") == []
        assert q.list_by_scope("scope3") == [ev.id]
        assert q.list_by_scope("scope4") == [ev.id]

    def test_update_audit_trail(self) -> None:
        """Test that update adds audit entry."""
        q = EventQueue()
        ev = make_sleep_event("actor1", 10)
        q.publish(ev)

        initial_audit_count = len(ev.audit)
        updated_ev = ev.model_copy(update={"priority": 75})
        q.update(updated_ev)

        assert len(updated_ev.audit) == initial_audit_count + 1
        audit_entry = updated_ev.audit[-1]
        assert audit_entry["actor_id"] == "system"
        assert audit_entry["action"] == "update"

    def test_update_preserves_event_id(self) -> None:
        """Test that update preserves the event ID."""
        q = EventQueue()
        ev = Event(type="TestEvent", id="preserved_id", audience_scope=["shipwide"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"type": "UpdatedEvent"})
        q.update(updated_ev)

        assert updated_ev.id == "preserved_id"
        assert q.get_by_id("preserved_id") is updated_ev

    def test_update_multiple_times(self) -> None:
        """Test updating the same event multiple times."""
        q = EventQueue()
        ev = Event(type="TestEvent", priority=50, audience_scope=["shipwide"])
        q.publish(ev)

        # First update
        updated1 = ev.model_copy(update={"priority": 75})
        q.update(updated1)

        # Second update
        updated2 = updated1.model_copy(update={"priority": 100})
        q.update(updated2)

        # Third update
        updated3 = updated2.model_copy(update={"state": "active"})
        q.update(updated3)

        final_ev = q.get_by_id(ev.id)
        assert final_ev.priority == 100
        assert final_ev.state == "active"
        assert len(final_ev.audit) == 3  # Three updates

    def test_update_with_complex_payload(self) -> None:
        """Test updating event with complex payload data."""
        q = EventQueue()
        ev = Event(type="TestEvent", payload={"simple": "value"}, audience_scope=["shipwide"])
        q.publish(ev)

        complex_payload = {
            "nested": {"key": "value", "number": 42},
            "list": [1, 2, 3],
            "boolean": True,
            "null_value": None,
        }
        updated_ev = ev.model_copy(update={"payload": complex_payload})
        q.update(updated_ev)

        stored_ev = q.get_by_id(ev.id)
        assert stored_ev.payload == complex_payload

    def test_update_removes_old_indexes(self) -> None:
        """Test that update properly removes old indexes."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="old_cat", audience_scope=["old_scope"])
        q.publish(ev)

        # Verify initial indexes
        assert q.list_by_category("old_cat") == [ev.id]
        assert q.list_by_scope("old_scope") == [ev.id]

        # Update to remove category and change scope
        updated_ev = ev.model_copy(update={"category": None, "audience_scope": ["new_scope"]})
        q.update(updated_ev)

        # Verify old indexes are removed
        assert q.list_by_category("old_cat") == []
        assert q.list_by_scope("old_scope") == []

        # Verify new indexes are created
        assert q.list_by_scope("new_scope") == [ev.id]

    def test_update_with_empty_strings(self) -> None:
        """Test updating with empty string values."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="old_cat", audience_scope=["old_scope"])
        q.publish(ev)

        updated_ev = ev.model_copy(update={"category": "", "audience_scope": [""]})
        q.update(updated_ev)

        # Empty string category is falsy, so it's not indexed
        assert q.list_by_category("") == []
        assert q.list_by_scope("") == [ev.id]
        assert q.list_by_category("old_cat") == []
        assert q.list_by_scope("old_scope") == []
