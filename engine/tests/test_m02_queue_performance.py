"""Performance tests for EventQueue."""

from __future__ import annotations

import time

import pytest

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_sleep_event


class TestEventQueuePerformance:
    """Performance tests for EventQueue operations."""

    def test_publish_performance(self) -> None:
        """Test publish performance with large number of events."""
        q = EventQueue(capacity=10000)

        start_time = time.perf_counter()

        for i in range(1000):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should be able to publish 1000 events in reasonable time
        assert duration < 1.0  # Less than 1 second
        assert len(q._events) == 1000

    def test_retrieval_performance(self) -> None:
        """Test retrieval performance with large dataset."""
        q = EventQueue(capacity=10000)

        # Create events with various categories and scopes
        categories = [f"cat{i}" for i in range(10)]
        scopes = [f"scope{i}" for i in range(10)]

        for i in range(1000):
            category = categories[i % len(categories)]
            scope = scopes[i % len(scopes)]
            ev = Event(type=f"Event{i}", category=category, audience_scope=[scope])
            q.publish(ev)

        # Test retrieval performance
        start_time = time.perf_counter()

        for _ in range(100):
            for category in categories:
                events = q.list_by_category(category)
                assert len(events) > 0

            for scope in scopes:
                events = q.list_by_scope(scope)
                assert len(events) > 0

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should be able to perform 100 retrieval cycles quickly
        assert duration < 1.0  # Less than 1 second

    def test_update_performance(self) -> None:
        """Test update performance with many updates."""
        q = EventQueue(capacity=10000)

        # Create initial events
        events = []
        for i in range(1000):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)
            events.append(ev)

        # Test update performance
        start_time = time.perf_counter()

        for i, ev in enumerate(events):
            updated_ev = ev.model_copy(update={"priority": 75 + (i % 25)})
            q.update(updated_ev)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should be able to update 1000 events in reasonable time
        assert duration < 2.0  # Less than 2 seconds

    def test_mixed_operations_performance(self) -> None:
        """Test performance of mixed publish/update/retrieve operations."""
        q = EventQueue(capacity=10000)

        start_time = time.perf_counter()

        # Mix of operations
        for i in range(500):
            # Publish new event
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

            # Update every 10th event
            if i % 10 == 0 and i > 0:
                prev_ev = q.get_by_id(ev.id)
                if prev_ev:
                    updated_ev = prev_ev.model_copy(update={"priority": 80})
                    q.update(updated_ev)

            # Retrieve by category every 20th event
            if i % 20 == 0:
                events = q.list_by_category("crew_admin")
                assert len(events) > 0

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should handle mixed operations efficiently
        assert duration < 2.0  # Less than 2 seconds

    def test_large_payload_performance(self) -> None:
        """Test performance with large payload data."""
        q = EventQueue(capacity=1000)

        # Create large payload
        large_payload = {
            "data": "x" * 10000,  # 10KB string
            "numbers": list(range(10000)),
            "nested": {
                f"level{i}": {f"key{j}": f"value_{i}_{j}" for j in range(100)} for i in range(10)
            },
        }

        start_time = time.perf_counter()

        for i in range(100):
            ev = Event(type=f"LargeEvent{i}", payload=large_payload, audience_scope=["shipwide"])
            q.publish(ev)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should handle large payloads reasonably well
        assert duration < 5.0  # Less than 5 seconds
        assert len(q._events) == 100

    def test_memory_usage_stability(self) -> None:
        """Test that memory usage remains stable with many operations."""
        q = EventQueue(capacity=10000)

        # Perform many operations to test memory stability
        for batch in range(10):
            # Publish batch of events
            for i in range(100):
                ev = make_sleep_event(f"actor_{batch}_{i}", 10)
                q.publish(ev)

            # Update some events
            for i in range(0, 100, 10):
                ev_id = f"actor_{batch}_{i}"
                ev = q.get_by_id(ev_id)
                if ev:
                    updated_ev = ev.model_copy(update={"priority": 90})
                    q.update(updated_ev)

            # Retrieve events
            for category in ["crew_admin"]:
                events = q.list_by_category(category)
                assert len(events) > 0

        # Should have processed all events successfully
        assert len(q._events) == 1000

    def test_concurrent_access_simulation(self) -> None:
        """Simulate concurrent access patterns."""
        q = EventQueue(capacity=10000)

        # Simulate different access patterns
        operations = []

        # Publisher pattern
        for i in range(200):
            ev = make_sleep_event(f"publisher_{i}", 10)
            operations.append(("publish", ev))

        # Updater pattern
        for i in range(100):
            ev = make_sleep_event(f"updater_{i}", 10)
            operations.append(("publish", ev))
            operations.append(("update", ev))

        # Reader pattern
        for i in range(50):
            ev = make_sleep_event(f"reader_{i}", 10)
            operations.append(("publish", ev))
            operations.append(("read", ev))

        start_time = time.perf_counter()

        for op_type, ev in operations:
            if op_type == "publish":
                q.publish(ev)
            elif op_type == "update":
                updated_ev = ev.model_copy(update={"priority": 85})
                q.update(updated_ev)
            elif op_type == "read":
                retrieved = q.get_by_id(ev.id)
                assert retrieved is not None

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should handle mixed access patterns efficiently
        assert duration < 3.0  # Less than 3 seconds

    def test_indexing_performance(self) -> None:
        """Test performance of indexing operations."""
        q = EventQueue(capacity=10000)

        # Create events with many different categories and scopes
        categories = [f"category_{i}" for i in range(100)]
        scopes = [f"scope_{i}" for i in range(100)]

        for i in range(1000):
            category = categories[i % len(categories)]
            scope = scopes[i % len(scopes)]
            ev = Event(type=f"Event{i}", category=category, audience_scope=[scope])
            q.publish(ev)

        start_time = time.perf_counter()

        # Test indexing performance
        for _ in range(10):
            for category in categories:
                events = q.list_by_category(category)
                assert len(events) > 0

            for scope in scopes:
                events = q.list_by_scope(scope)
                assert len(events) > 0

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Indexing should be fast even with many categories/scopes
        assert duration < 2.0  # Less than 2 seconds

    def test_capacity_boundary_performance(self) -> None:
        """Test performance at capacity boundaries."""
        capacity = 1000
        q = EventQueue(capacity=capacity)

        # Fill to capacity
        start_time = time.perf_counter()

        for i in range(capacity):
            ev = make_sleep_event(f"actor{i}", 10)
            q.publish(ev)

        # Test operations at capacity
        for i in range(100):
            # Try to publish beyond capacity (should fail quickly)
            with pytest.raises(RuntimeError):
                ev = make_sleep_event(f"overflow_{i}", 10)
                q.publish(ev)

            # Update existing events
            ev_id = f"actor{i % capacity}"
            ev = q.get_by_id(ev_id)
            if ev:
                updated_ev = ev.model_copy(update={"priority": 95})
                q.update(updated_ev)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should handle capacity boundary operations efficiently
        assert duration < 2.0  # Less than 2 seconds
        assert len(q._events) == capacity
