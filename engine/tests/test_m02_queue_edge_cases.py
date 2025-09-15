"""Comprehensive tests for EventQueue edge cases and boundary conditions."""

from __future__ import annotations

from engine.m02_events import Event, EventQueue


class TestEventQueueEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_category(self) -> None:
        """Test handling of empty string category (not indexed)."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="", audience_scope=["shipwide"])
        q.publish(ev)

        events = q.list_by_category("")
        # Empty string category is falsy, so it's not indexed
        assert events == []

    def test_empty_string_scope(self) -> None:
        """Test handling of empty string scope."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=[""])
        q.publish(ev)

        events = q.list_by_scope("")
        assert events == [ev.id]

    def test_very_long_event_id(self) -> None:
        """Test handling of very long event IDs."""
        q = EventQueue()
        long_id = "x" * 1000
        ev = Event(type="TestEvent", id=long_id, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(long_id)
        assert retrieved is ev

    def test_special_characters_in_scope(self) -> None:
        """Test handling of special characters in scope."""
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
            events = q.list_by_scope(scope)
            assert events == [ev.id]

    def test_unicode_characters(self) -> None:
        """Test handling of unicode characters."""
        q = EventQueue()
        unicode_scope = "scope_测试_🌍"
        ev = Event(type="TestEvent", audience_scope=[unicode_scope])
        q.publish(ev)

        events = q.list_by_scope(unicode_scope)
        assert events == [ev.id]

    def test_none_values_handling(self) -> None:
        """Test handling of None values in various fields."""
        q = EventQueue()
        ev = Event(
            type="TestEvent",
            category=None,
            audience_scope=["shipwide"],  # Must have audience scope
            issuer=None,
            taker=None,
        )
        q.publish(ev)

        assert q.get_by_id(ev.id) is ev
        assert q.list_by_category("any_category") == []
        assert q.list_by_scope("shipwide") == [ev.id]

    def test_duplicate_scope_handling(self) -> None:
        """Test handling of duplicate scopes in same event."""
        q = EventQueue()
        ev = Event(type="TestEvent", audience_scope=["scope1", "scope1"])
        q.publish(ev)

        events = q.list_by_scope("scope1")
        assert len(events) == 2  # Should contain duplicate entries
        assert events == [ev.id, ev.id]

    def test_duplicate_category_handling(self) -> None:
        """Test that category creates duplicates when same event is published twice."""
        q = EventQueue()
        ev = Event(type="TestEvent", category="test_category", audience_scope=["shipwide"])
        q.publish(ev)

        # Try to publish same event again (creates duplicate in index)
        q.publish(ev)

        events = q.list_by_category("test_category")
        assert len(events) == 2  # Creates duplicates in the index
        assert events == [ev.id, ev.id]

    def test_very_large_payload(self) -> None:
        """Test handling of very large payload data."""
        q = EventQueue()
        large_payload = {
            "data": "x" * 10000,
            "numbers": list(range(10000)),
            "nested": {"level1": {"level2": {"level3": "deep"}}},
        }
        ev = Event(type="LargeEvent", payload=large_payload, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.payload == large_payload

    def test_event_with_all_none_optional_fields(self) -> None:
        """Test event with all optional fields set to None."""
        q = EventQueue()
        ev = Event(
            type="MinimalEvent",
            issuer=None,
            category=None,
            max_request_priority=None,
            deadline=None,
            ttl_seconds=None,
            taker=None,
            parent_id=None,
            group_id=None,
            idempotency_key=None,
            eta_s=None,
            severity=None,
            audience_scope=["shipwide"],
        )
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved is ev
        assert retrieved.issuer is None
        assert retrieved.category is None

    def test_event_with_empty_lists(self) -> None:
        """Test event with empty list fields (except audience_scope which must be non-empty)."""
        q = EventQueue()
        ev = Event(
            type="EmptyListsEvent",
            audience_scope=["shipwide"],  # Must have audience scope
            dependencies=[],
            qualifiers=[],
            preconditions=[],
        )
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.audience_scope == ["shipwide"]
        assert retrieved.dependencies == []
        assert retrieved.qualifiers == []
        assert retrieved.preconditions == []

    def test_event_with_whitespace_strings(self) -> None:
        """Test event with whitespace-only strings."""
        q = EventQueue()
        ev = Event(type="WhitespaceEvent", category="   ", audience_scope=["  ", "\t", "\n"])
        q.publish(ev)

        assert q.list_by_category("   ") == [ev.id]
        assert q.list_by_scope("  ") == [ev.id]
        assert q.list_by_scope("\t") == [ev.id]
        assert q.list_by_scope("\n") == [ev.id]

    def test_event_with_mixed_case_strings(self) -> None:
        """Test event with mixed case strings."""
        q = EventQueue()
        ev = Event(
            type="MixedCaseEvent",
            category="TestCategory",
            audience_scope=["TestScope", "testscope", "TESTSCOPE"],
        )
        q.publish(ev)

        assert q.list_by_category("TestCategory") == [ev.id]
        assert q.list_by_scope("TestScope") == [ev.id]
        assert q.list_by_scope("testscope") == [ev.id]
        assert q.list_by_scope("TESTSCOPE") == [ev.id]

    def test_event_with_numeric_strings(self) -> None:
        """Test event with numeric strings in category and scope."""
        q = EventQueue()
        ev = Event(type="NumericEvent", category="123", audience_scope=["456", "789"])
        q.publish(ev)

        assert q.list_by_category("123") == [ev.id]
        assert q.list_by_scope("456") == [ev.id]
        assert q.list_by_scope("789") == [ev.id]

    def test_event_with_special_json_characters(self) -> None:
        """Test event with special JSON characters."""
        q = EventQueue()
        special_payload = {
            "quotes": 'He said "Hello"',
            "backslashes": "C:\\path\\to\\file",
            "newlines": "Line 1\nLine 2",
            "tabs": "Column1\tColumn2",
            "unicode": "测试 🌍",
        }
        ev = Event(type="SpecialCharsEvent", payload=special_payload, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.payload == special_payload

    def test_event_with_extreme_values(self) -> None:
        """Test event with extreme numeric values."""
        q = EventQueue()
        ev = Event(
            type="ExtremeValuesEvent",
            priority=100,
            progress=1.0,
            team_size=999999,
            ttl_seconds=86400,
            eta_s=3600,
            audience_scope=["shipwide"],
        )
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.priority == 100
        assert retrieved.progress == 1.0
        assert retrieved.team_size == 999999
        assert retrieved.ttl_seconds == 86400
        assert retrieved.eta_s == 3600

    def test_event_with_very_long_strings(self) -> None:
        """Test event with very long string values."""
        q = EventQueue()
        long_string = "x" * 10000
        ev = Event(
            type="LongStringsEvent",
            category=long_string,
            audience_scope=[long_string],
            issuer=long_string,
        )
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.category == long_string
        assert retrieved.audience_scope == [long_string]
        assert retrieved.issuer == long_string

    def test_event_with_deeply_nested_payload(self) -> None:
        """Test event with deeply nested payload structure."""
        q = EventQueue()
        nested_payload = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        ev = Event(type="NestedEvent", payload=nested_payload, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.payload == nested_payload

    def test_event_with_circular_references_in_payload(self) -> None:
        """Test event with circular references in payload (should handle gracefully)."""
        q = EventQueue()
        circular_data = {}
        circular_data["self"] = circular_data

        # This should not raise an error during publish
        ev = Event(type="CircularEvent", payload=circular_data, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        # Pydantic serialization/deserialization breaks circular references
        # So we can't test for exact identity, but structure should be preserved
        assert "self" in retrieved.payload
        assert isinstance(retrieved.payload["self"], dict)

    def test_event_with_boolean_values(self) -> None:
        """Test event with boolean values in payload."""
        q = EventQueue()
        boolean_payload = {"true_value": True, "false_value": False, "mixed": [True, False, True]}
        ev = Event(type="BooleanEvent", payload=boolean_payload, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.payload == boolean_payload

    def test_event_with_float_values(self) -> None:
        """Test event with various float values."""
        q = EventQueue()
        float_payload = {
            "positive": 3.14159,
            "negative": -2.71828,
            "zero": 0.0,
            "very_small": 1e-10,
            "very_large": 1e10,
        }
        ev = Event(type="FloatEvent", payload=float_payload, audience_scope=["shipwide"])
        q.publish(ev)

        retrieved = q.get_by_id(ev.id)
        assert retrieved.payload == float_payload
