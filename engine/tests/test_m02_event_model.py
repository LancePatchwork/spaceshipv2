from __future__ import annotations

import time
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from engine.m02_events import Event, new_ulid


class TestEventCreation:
    """Comprehensive tests for Event object creation and initialization."""

    def test_event_autofills_id_and_ts(self) -> None:
        """Test that Event automatically generates ULID and timestamp."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        assert len(ev.id) == 26
        assert isinstance(ev.ts_ms, int)
        assert ev.ts_ms > 0

    def test_event_with_custom_id_and_timestamp(self) -> None:
        """Test Event creation with explicitly provided ID and timestamp."""
        custom_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        custom_ts = 1234567890000
        ev = Event(type="TestEvent", id=custom_id, ts_ms=custom_ts, audience_scope=["shipwide"])
        assert ev.id == custom_id
        assert ev.ts_ms == custom_ts

    def test_event_with_all_optional_fields(self) -> None:
        """Test Event creation with all optional fields populated."""
        deadline = datetime.now() + timedelta(hours=1)
        ev = Event(
            type="ComplexEvent",
            issuer="system",
            audience_scope=["bridge", "engineering"],
            category="emergency",
            priority=75,
            max_request_priority=90,
            preemptible=False,
            deadline=deadline,
            ttl_seconds=3600,
            dependencies=["dep1", "dep2"],
            state="routed",
            taker="crew_member_1",
            team_size=3,
            parent_id="parent_event_123",
            group_id="group_456",
            idempotency_key="unique_key_789",
            progress=0.25,
            eta_s=1800,
            severity="critical",
            qualifiers=["urgent", "high_priority"],
            preconditions=["power_available", "crew_awake"],
            payload={"data": "important", "count": 42},
        )

        assert ev.type == "ComplexEvent"
        assert ev.issuer == "system"
        assert ev.audience_scope == ["bridge", "engineering"]
        assert ev.category == "emergency"
        assert ev.priority == 75
        assert ev.max_request_priority == 90
        assert ev.preemptible is False
        assert ev.deadline == deadline
        assert ev.ttl_seconds == 3600
        assert ev.dependencies == ["dep1", "dep2"]
        assert ev.state == "routed"
        assert ev.taker == "crew_member_1"
        assert ev.team_size == 3
        assert ev.parent_id == "parent_event_123"
        assert ev.group_id == "group_456"
        assert ev.idempotency_key == "unique_key_789"
        assert ev.progress == 0.25
        assert ev.eta_s == 1800
        assert ev.severity == "critical"
        assert ev.qualifiers == ["urgent", "high_priority"]
        assert ev.preconditions == ["power_available", "crew_awake"]
        assert ev.payload == {"data": "important", "count": 42}

    def test_event_default_values(self) -> None:
        """Test that Event uses correct default values."""
        ev = Event(type="DefaultEvent", audience_scope=["shipwide"])
        assert ev.issuer is None
        assert ev.audience_scope == ["shipwide"]
        assert ev.category is None
        assert ev.priority == 50
        assert ev.max_request_priority is None
        assert ev.preemptible is True
        assert ev.deadline is None
        assert ev.ttl_seconds is None
        assert ev.dependencies == []
        assert ev.state == "queued"
        assert ev.taker is None
        assert ev.team_size == 1
        assert ev.parent_id is None
        assert ev.group_id is None
        assert ev.idempotency_key is None
        assert ev.progress == 0.0
        assert ev.eta_s is None
        assert ev.severity is None
        assert ev.qualifiers == []
        assert ev.preconditions == []
        assert ev.payload == {}
        assert ev.audit == []


class TestEventValidation:
    """Comprehensive validation tests for Event fields."""

    def test_priority_validation_valid_range(self) -> None:
        """Test priority validation with valid values."""
        for priority in [0, 25, 50, 75, 100]:
            ev = Event(type="TestEvent", priority=priority, audience_scope=["shipwide"])
            assert ev.priority == priority

    def test_priority_validation_invalid_low(self) -> None:
        """Test priority validation with values below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            Event(type="TestEvent", priority=-1, audience_scope=["shipwide"])
        assert "priority must be between 0 and 100" in str(exc_info.value)

    def test_priority_validation_invalid_high(self) -> None:
        """Test priority validation with values above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            Event(type="TestEvent", priority=101, audience_scope=["shipwide"])
        assert "priority must be between 0 and 100" in str(exc_info.value)

    def test_progress_validation_valid_range(self) -> None:
        """Test progress validation with valid values."""
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            ev = Event(type="TestEvent", progress=progress, audience_scope=["shipwide"])
            assert ev.progress == progress

    def test_progress_validation_invalid_low(self) -> None:
        """Test progress validation with values below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            Event(type="TestEvent", progress=-0.1, audience_scope=["shipwide"])
        assert "progress must be between 0 and 1" in str(exc_info.value)

    def test_progress_validation_invalid_high(self) -> None:
        """Test progress validation with values above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            Event(type="TestEvent", progress=1.1, audience_scope=["shipwide"])
        assert "progress must be between 0 and 1" in str(exc_info.value)

    def test_state_validation_valid_states(self) -> None:
        """Test state validation with all valid state values."""
        valid_states = [
            "queued",
            "routed",
            "claimed",
            "active",
            "suspended",
            "done",
            "failed",
            "expired",
            "cancelled",
        ]
        for state in valid_states:
            ev = Event(type="TestEvent", state=state, audience_scope=["shipwide"])
            assert ev.state == state

    def test_state_validation_invalid_state(self) -> None:
        """Test state validation with invalid state value."""
        with pytest.raises(ValidationError):
            Event(type="TestEvent", state="invalid_state", audience_scope=["shipwide"])

    def test_severity_validation_valid_severities(self) -> None:
        """Test severity validation with all valid severity values."""
        valid_severities = ["info", "warn", "critical"]
        for severity in valid_severities:
            ev = Event(type="TestEvent", severity=severity, audience_scope=["shipwide"])
            assert ev.severity == severity

    def test_severity_validation_invalid_severity(self) -> None:
        """Test severity validation with invalid severity value."""
        with pytest.raises(ValidationError):
            Event(type="TestEvent", severity="invalid_severity", audience_scope=["shipwide"])

    def test_team_size_accepts_any_integer(self) -> None:
        """Test team_size accepts any integer value (no validation currently implemented)."""
        # Valid team sizes
        for size in [1, 5, 10, 100]:
            ev = Event(type="TestEvent", team_size=size, audience_scope=["shipwide"])
            assert ev.team_size == size

        # Note: Currently no validation for team_size, so these should work
        # This test documents current behavior - validation could be added later
        ev_zero = Event(type="TestEvent", team_size=0, audience_scope=["shipwide"])
        assert ev_zero.team_size == 0

        ev_negative = Event(type="TestEvent", team_size=-1, audience_scope=["shipwide"])
        assert ev_negative.team_size == -1


class TestEventAudit:
    """Comprehensive tests for Event audit functionality."""

    def test_append_audit_basic(self) -> None:
        """Test basic audit entry creation."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        ev.append_audit("actor1", "claimed", {"k": "v"})
        assert len(ev.audit) == 1
        entry = ev.audit[0]
        assert entry["actor_id"] == "actor1"
        assert entry["action"] == "claimed"
        assert entry["details"] == {"k": "v"}
        assert isinstance(entry["ts"], int)
        # verify timestamp parses
        datetime.fromtimestamp(entry["ts"] / 1000)

    def test_append_audit_multiple_entries(self) -> None:
        """Test multiple audit entries are appended correctly."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])

        # Add multiple audit entries
        ev.append_audit("actor1", "created", {"source": "system"})
        ev.append_audit("actor2", "claimed", {"priority": "high"})
        ev.append_audit("actor1", "completed", {"result": "success"})

        assert len(ev.audit) == 3

        # Check first entry
        assert ev.audit[0]["actor_id"] == "actor1"
        assert ev.audit[0]["action"] == "created"
        assert ev.audit[0]["details"] == {"source": "system"}

        # Check second entry
        assert ev.audit[1]["actor_id"] == "actor2"
        assert ev.audit[1]["action"] == "claimed"
        assert ev.audit[1]["details"] == {"priority": "high"}

        # Check third entry
        assert ev.audit[2]["actor_id"] == "actor1"
        assert ev.audit[2]["action"] == "completed"
        assert ev.audit[2]["details"] == {"result": "success"}

    def test_append_audit_without_details(self) -> None:
        """Test audit entry creation without details."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        ev.append_audit("actor1", "claimed")
        assert len(ev.audit) == 1
        entry = ev.audit[0]
        assert entry["actor_id"] == "actor1"
        assert entry["action"] == "claimed"
        assert entry["details"] == {}

    def test_append_audit_with_none_details(self) -> None:
        """Test audit entry creation with None details."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        ev.append_audit("actor1", "claimed", None)
        assert len(ev.audit) == 1
        entry = ev.audit[0]
        assert entry["actor_id"] == "actor1"
        assert entry["action"] == "claimed"
        assert entry["details"] == {}

    def test_append_audit_timestamp_ordering(self) -> None:
        """Test that audit entries maintain chronological order."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])

        # Add entries with small delays to ensure different timestamps
        ev.append_audit("actor1", "first")
        time.sleep(0.001)  # 1ms delay
        ev.append_audit("actor2", "second")
        time.sleep(0.001)  # 1ms delay
        ev.append_audit("actor3", "third")

        assert len(ev.audit) == 3
        assert ev.audit[0]["ts"] <= ev.audit[1]["ts"] <= ev.audit[2]["ts"]

    def test_append_audit_complex_details(self) -> None:
        """Test audit entry with complex details structure."""
        ev = Event(type="TestEvent", audience_scope=["shipwide"])
        complex_details = {
            "nested": {"key": "value", "number": 42},
            "list": [1, 2, 3],
            "boolean": True,
            "null_value": None,
            "string": "test",
        }
        ev.append_audit("actor1", "complex_action", complex_details)

        assert len(ev.audit) == 1
        entry = ev.audit[0]
        assert entry["details"] == complex_details


class TestEventAudienceScope:
    """Tests for audience scope validation and error handling."""

    def test_empty_audience_scope_error(self) -> None:
        """Test that empty audience scope raises a comprehensive validation error."""
        with pytest.raises(ValueError) as exc_info:
            Event(type="TestEvent", audience_scope=[])

        error_message = str(exc_info.value)
        # Check that the error message contains key debugging information
        assert "Event audience_scope cannot be empty" in error_message
        assert "will never be routed to any actors" in error_message
        assert "stuck in 'queued' state" in error_message
        assert "bug in event creation" in error_message
        assert "shipwide" in error_message
        assert "officers" in error_message
        assert "department:" in error_message
        assert "private:" in error_message

    def test_non_empty_audience_scope_no_error(self) -> None:
        """Test that non-empty audience scope doesn't trigger error."""
        ev = Event(type="TestEvent", audience_scope=["bridge", "engineering"])
        assert ev.audience_scope == ["bridge", "engineering"]

    def test_audience_scope_preservation(self) -> None:
        """Test that audience scope values are preserved correctly."""
        scope = ["bridge", "engineering", "medical", "security"]
        ev = Event(type="TestEvent", audience_scope=scope)
        assert ev.audience_scope == scope


class TestULIDGeneration:
    """Tests for ULID generation functionality."""

    def test_ulid_format(self) -> None:
        """Test that generated ULIDs have correct format."""
        ulid = new_ulid()
        assert len(ulid) == 26
        assert ulid.isalnum()
        # ULID should only contain valid characters
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        assert all(c in valid_chars for c in ulid)

    def test_ulid_uniqueness(self) -> None:
        """Test that generated ULIDs are unique."""
        ulids = [new_ulid() for _ in range(100)]
        assert len(set(ulids)) == 100  # All should be unique

    def test_ulid_timestamp_ordering(self) -> None:
        """Test that ULIDs maintain timestamp ordering."""
        ulid1 = new_ulid()
        time.sleep(0.001)  # Small delay
        ulid2 = new_ulid()
        # ULIDs should be sortable by timestamp
        assert ulid1 < ulid2

    def test_ulid_lexicographic_ordering(self) -> None:
        """Test that ULIDs are lexicographically sortable."""
        ulids = [new_ulid() for _ in range(10)]
        sorted_ulids = sorted(ulids)
        assert ulids != sorted_ulids  # Original order should be different
        assert sorted_ulids == sorted(ulids)  # Sorted should be consistent


class TestEventSerialization:
    """Tests for Event serialization and deserialization."""

    def test_event_to_dict(self) -> None:
        """Test converting Event to dictionary."""
        ev = Event(
            type="TestEvent", priority=75, payload={"key": "value"}, audience_scope=["bridge"]
        )
        data = ev.model_dump()

        assert isinstance(data, dict)
        assert data["type"] == "TestEvent"
        assert data["priority"] == 75
        assert data["payload"] == {"key": "value"}
        assert data["audience_scope"] == ["bridge"]
        assert "id" in data
        assert "ts_ms" in data

    def test_event_from_dict(self) -> None:
        """Test creating Event from dictionary."""
        data = {
            "type": "TestEvent",
            "priority": 75,
            "payload": {"key": "value"},
            "audience_scope": ["bridge"],
            "state": "active",
        }
        ev = Event.model_validate(data)

        assert ev.type == "TestEvent"
        assert ev.priority == 75
        assert ev.payload == {"key": "value"}
        assert ev.audience_scope == ["bridge"]
        assert ev.state == "active"

    def test_event_json_serialization(self) -> None:
        """Test Event JSON serialization."""
        ev = Event(
            type="TestEvent",
            priority=75,
            payload={"key": "value", "number": 42},
            audience_scope=["shipwide"],
        )
        json_str = ev.model_dump_json()

        assert isinstance(json_str, str)
        assert "TestEvent" in json_str
        assert "75" in json_str
        assert "key" in json_str

    def test_event_json_deserialization(self) -> None:
        """Test Event JSON deserialization."""
        json_str = (
            '{"type": "TestEvent", "priority": 75, "payload": {"key": "value"}, '
            '"audience_scope": ["shipwide"]}'
        )
        ev = Event.model_validate_json(json_str)

        assert ev.type == "TestEvent"
        assert ev.priority == 75
        assert ev.payload == {"key": "value"}


class TestEventEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_event_with_maximum_values(self) -> None:
        """Test Event with maximum allowed values."""
        ev = Event(
            type="MaxEvent",
            priority=100,
            progress=1.0,
            team_size=1000,
            ttl_seconds=86400,
            eta_s=3600,
            audience_scope=["shipwide"],
        )
        assert ev.priority == 100
        assert ev.progress == 1.0
        assert ev.team_size == 1000
        assert ev.ttl_seconds == 86400
        assert ev.eta_s == 3600

    def test_event_with_minimum_values(self) -> None:
        """Test Event with minimum allowed values."""
        ev = Event(
            type="MinEvent", priority=0, progress=0.0, team_size=1, audience_scope=["shipwide"]
        )
        assert ev.priority == 0
        assert ev.progress == 0.0
        assert ev.team_size == 1

    def test_event_with_large_payload(self) -> None:
        """Test Event with large payload data."""
        large_payload = {
            "data": "x" * 1000,
            "numbers": list(range(1000)),
            "nested": {"level1": {"level2": {"level3": "deep"}}},
        }
        ev = Event(type="LargeEvent", payload=large_payload, audience_scope=["shipwide"])
        assert ev.payload == large_payload

    def test_event_with_special_characters(self) -> None:
        """Test Event with special characters in strings."""
        ev = Event(
            type="SpecialEvent",
            issuer="user@domain.com",
            audience_scope=["bridge-crew", "engineering_team"],
            qualifiers=["high-priority", "urgent!"],
            payload={"message": "Hello, World! 🌍", "unicode": "测试"},
        )
        assert ev.issuer == "user@domain.com"
        assert "bridge-crew" in ev.audience_scope
        assert "urgent!" in ev.qualifiers
        assert ev.payload["message"] == "Hello, World! 🌍"
        assert ev.payload["unicode"] == "测试"
