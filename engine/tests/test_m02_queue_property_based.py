"""Property-based tests for EventQueue using Hypothesis."""

from __future__ import annotations

import string
from typing import List

import pytest
from hypothesis import given
from hypothesis import strategies as st

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_sleep_event


class TestEventQueuePropertyBased:
    """Property-based tests for EventQueue using Hypothesis."""

    @given(
        capacity=st.integers(min_value=0, max_value=1000),
        num_events=st.integers(min_value=0, max_value=100),
    )
    def test_capacity_property(self, capacity: int, num_events: int) -> None:
        """Test that queue never exceeds capacity."""
        q = EventQueue(capacity=capacity)

        for i in range(min(num_events, capacity)):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        # If we try to publish more than capacity, it should fail
        if num_events > capacity:
            with pytest.raises(RuntimeError, match="queue capacity exceeded"):
                ev = make_sleep_event(f"actor{capacity}", 10)
                q.publish(ev)

        # Queue should never exceed capacity
        assert len(q._events) <= capacity

    @given(
        categories=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
        scopes=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
        num_events=st.integers(min_value=1, max_value=50),
    )
    def test_indexing_consistency(
        self, categories: List[str], scopes: List[str], num_events: int
    ) -> None:
        """Test that indexing is consistent with published events."""
        q = EventQueue(capacity=1000)

        for i in range(num_events):
            category = categories[i % len(categories)]
            scope = scopes[i % len(scopes)]
            ev = Event(type=f"Event{i}", category=category, audience_scope=[scope])
            q.publish(ev)

        # Check that all events are indexed correctly
        for category in categories:
            events = q.list_by_category(category)
            # Count how many events should be in this category
            expected_count = sum(
                1 for i in range(num_events) if categories[i % len(categories)] == category
            )
            assert len(events) == expected_count

        for scope in scopes:
            events = q.list_by_scope(scope)
            # Count how many events should be in this scope
            expected_count = sum(1 for i in range(num_events) if scopes[i % len(scopes)] == scope)
            assert len(events) == expected_count

    @given(
        event_data=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),  # type
                st.text(min_size=0, max_size=20),  # category
                st.lists(
                    st.text(min_size=1, max_size=20), min_size=1, max_size=5
                ),  # scopes (must be non-empty)
                st.integers(min_value=0, max_value=100),  # priority
            ),
            min_size=1,
            max_size=20,
        )
    )
    def test_publish_retrieve_roundtrip(self, event_data: List[tuple]) -> None:
        """Test that published events can be retrieved correctly."""
        q = EventQueue(capacity=1000)
        published_events = []

        for event_type, category, scopes, priority in event_data:
            ev = Event(
                type=event_type,
                category=category if category else None,
                audience_scope=scopes,
                priority=priority,
            )
            q.publish(ev)
            published_events.append(ev)

        # Test that all events can be retrieved by ID
        for ev in published_events:
            retrieved = q.get_by_id(ev.id)
            assert retrieved is ev
            assert retrieved.type == ev.type
            assert retrieved.category == ev.category
            assert retrieved.audience_scope == ev.audience_scope
            assert retrieved.priority == ev.priority

    @given(
        initial_events=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10),
                st.text(min_size=0, max_size=10),
                st.lists(
                    st.text(min_size=1, max_size=10), min_size=1, max_size=3
                ),  # scopes must be non-empty
            ),
            min_size=1,
            max_size=10,
        ),
        updates=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=9),  # event index
                st.text(min_size=0, max_size=10),  # new category
                st.lists(
                    st.text(min_size=1, max_size=10), min_size=1, max_size=3
                ),  # new scopes must be non-empty
            ),
            min_size=1,
            max_size=5,
        ),
    )
    def test_update_consistency(self, initial_events: List[tuple], updates: List[tuple]) -> None:
        """Test that updates maintain consistency."""
        q = EventQueue(capacity=1000)
        events = []

        # Publish initial events
        for event_type, category, scopes in initial_events:
            ev = Event(
                type=event_type, category=category if category else None, audience_scope=scopes
            )
            q.publish(ev)
            events.append(ev)

        # Apply updates
        for event_idx, new_category, new_scopes in updates:
            if event_idx < len(events):
                ev = events[event_idx]
                updated_ev = ev.model_copy(
                    update={
                        "category": new_category if new_category else None,
                        "audience_scope": new_scopes,
                    }
                )
                q.update(updated_ev)
                events[event_idx] = updated_ev

        # Verify consistency
        for ev in events:
            retrieved = q.get_by_id(ev.id)
            assert retrieved is ev
            assert retrieved.category == ev.category
            assert retrieved.audience_scope == ev.audience_scope

    @given(
        text_data=st.text(
            min_size=1, max_size=100, alphabet=string.printable
        ),  # Must be non-empty for scope
        num_events=st.integers(min_value=1, max_value=10),
    )
    def test_unicode_and_special_characters(self, text_data: str, num_events: int) -> None:
        """Test handling of unicode and special characters."""
        q = EventQueue(capacity=1000)

        for i in range(num_events):
            ev = Event(
                type=f"Event{i}_{text_data}",
                category=text_data if text_data else None,
                audience_scope=[text_data],  # text_data is guaranteed non-empty
            )
            q.publish(ev)

        # Test retrieval
        category_events = q.list_by_category(text_data)
        scope_events = q.list_by_scope(text_data)
        assert len(category_events) == num_events
        assert len(scope_events) == num_events

    @given(
        payload_data=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.one_of(
                st.text(),
                st.integers(),
                st.floats(),
                st.booleans(),
                st.none(),
                st.lists(st.integers(), min_size=0, max_size=10),
                st.dictionaries(
                    st.text(min_size=1, max_size=5),
                    st.one_of(st.text(), st.integers()),
                    min_size=0,
                    max_size=5,
                ),
            ),
            min_size=0,
            max_size=10,
        ),
        num_events=st.integers(min_value=1, max_value=5),
    )
    def test_complex_payload_handling(self, payload_data, num_events: int) -> None:
        """Test handling of complex payload data."""
        q = EventQueue(capacity=1000)

        for i in range(num_events):
            ev = Event(type=f"PayloadEvent{i}", payload=payload_data, audience_scope=["shipwide"])
            q.publish(ev)

        # Verify all events can be retrieved with correct payload
        for i in range(num_events):
            # Find our event by type (since events without category aren't indexed)
            our_event = None
            for event_id, event in q._events.items():
                if event.type == f"PayloadEvent{i}":
                    our_event = event
                    break

            assert our_event is not None
            assert our_event.payload == payload_data

    @given(
        capacity=st.integers(min_value=1, max_value=100),
        num_operations=st.integers(min_value=1, max_value=50),
    )
    def test_capacity_under_stress(self, capacity: int, num_operations: int) -> None:
        """Test capacity limits under various operation sequences."""
        q = EventQueue(capacity=capacity)

        for i in range(num_operations):
            try:
                ev = make_sleep_event(f"actor{i}", 10)
                q.publish(ev)
            except RuntimeError:
                # Expected when capacity is exceeded
                pass

        # Queue should never exceed capacity
        assert len(q._events) <= capacity

    @given(
        event_ids=st.lists(
            st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits),
            min_size=1,
            max_size=20,
            unique=True,
        )
    )
    def test_unique_event_ids(self, event_ids: List[str]) -> None:
        """Test that unique event IDs work correctly."""
        q = EventQueue(capacity=1000)

        for event_id in event_ids:
            ev = Event(type="TestEvent", id=event_id, audience_scope=["shipwide"])
            q.publish(ev)

        # All events should be retrievable by their IDs
        for event_id in event_ids:
            retrieved = q.get_by_id(event_id)
            assert retrieved is not None
            assert retrieved.id == event_id

        # Should have exactly as many events as unique IDs
        assert len(q._events) == len(event_ids)
