"""Comprehensive tests for EventQueue initialization and configuration."""

from __future__ import annotations

from engine.m02_events import EventQueue


class TestEventQueueInitialization:
    """Tests for EventQueue initialization with various configurations."""

    def test_default_initialization(self) -> None:
        """Test EventQueue with default parameters."""
        q = EventQueue()
        assert q.capacity == 10_000
        assert len(q._events) == 0
        assert len(q._by_category) == 0
        assert len(q._by_scope) == 0

    def test_custom_capacity_initialization(self) -> None:
        """Test EventQueue with custom capacity."""
        q = EventQueue(capacity=100)
        assert q.capacity == 100
        assert len(q._events) == 0

    def test_zero_capacity_initialization(self) -> None:
        """Test EventQueue with zero capacity."""
        q = EventQueue(capacity=0)
        assert q.capacity == 0
        assert len(q._events) == 0

    def test_large_capacity_initialization(self) -> None:
        """Test EventQueue with very large capacity."""
        q = EventQueue(capacity=1_000_000)
        assert q.capacity == 1_000_000
        assert len(q._events) == 0

    def test_negative_capacity_initialization(self) -> None:
        """Test EventQueue with negative capacity (edge case)."""
        q = EventQueue(capacity=-1)
        assert q.capacity == -1
        assert len(q._events) == 0

    def test_very_small_capacity_initialization(self) -> None:
        """Test EventQueue with very small capacity."""
        q = EventQueue(capacity=1)
        assert q.capacity == 1
        assert len(q._events) == 0

    def test_capacity_type_validation(self) -> None:
        """Test that capacity accepts integer values."""
        # These should not raise errors
        q1 = EventQueue(capacity=42)
        q2 = EventQueue(capacity=0)
        q3 = EventQueue(capacity=999999)

        assert q1.capacity == 42
        assert q2.capacity == 0
        assert q3.capacity == 999999

    def test_multiple_queue_instances(self) -> None:
        """Test that multiple queue instances are independent."""
        q1 = EventQueue(capacity=10)
        q2 = EventQueue(capacity=20)

        assert q1.capacity == 10
        assert q2.capacity == 20
        assert q1 is not q2
        assert q1._events is not q2._events
        assert q1._by_category is not q2._by_category
        assert q1._by_scope is not q2._by_scope

    def test_queue_state_after_initialization(self) -> None:
        """Test internal state of queue after initialization."""
        q = EventQueue(capacity=50)

        # Check that all internal structures are properly initialized
        assert isinstance(q._events, dict)
        assert isinstance(q._by_category, dict)
        assert isinstance(q._by_scope, dict)

        # Check that they are empty
        assert len(q._events) == 0
        assert len(q._by_category) == 0
        assert len(q._by_scope) == 0

        # Check that they are mutable
        q._events["test"] = "value"
        assert "test" in q._events
