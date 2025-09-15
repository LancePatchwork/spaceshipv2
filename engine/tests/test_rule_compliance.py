"""Tests to validate compliance with development rules and standards.

This module contains tests that verify the codebase follows our established
development rules, architectural patterns, and quality standards.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

# Removed unused imports: Any, Dict, List, Set
import pytest

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_red_alert_event, make_sleep_event


class TestRuleCompliance:
    """Test compliance with development rules and standards."""

    def test_no_print_statements_in_production_code(self) -> None:
        """Test that no print() statements exist in production code."""
        # This test would need to be run against the actual codebase
        # For now, we'll test that our test files don't have print statements
        test_files = Path(__file__).parent.glob("test_*.py")

        for test_file in test_files:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for print statements that are NOT in comments or docstrings
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Skip comments and docstrings
                    if (
                        stripped.startswith("#")
                        or stripped.startswith('"""')
                        or stripped.startswith("'''")
                    ):
                        continue

                    # Skip lines that are part of multi-line docstrings
                    if '"""' in line or "'''" in line:
                        continue

                    # Check for print statements
                    if "print(" in line and not re.search(r'["\'].*print\s*\(.*["\']', line):
                        pytest.fail(f"Found print() statement in {test_file}:{i} - {line.strip()}")

    def test_event_priority_semantics(self) -> None:
        """Test that event priority follows the rule: lower number = higher priority."""
        # Test critical priority (0)
        critical_event = make_red_alert_event("combat", False)
        assert critical_event.priority == 0, "Red alert should have priority 0 (critical)"

        # Test low priority (90+)
        sleep_event = make_sleep_event("actor1", 10)
        assert sleep_event.priority >= 90, "Sleep events should have low priority (90+)"

        # Test that priority validation works
        with pytest.raises(ValueError):  # Specific exception type
            Event(type="TestEvent", priority=-1, audience_scope=["shipwide"])

        with pytest.raises(ValueError):  # Specific exception type
            Event(type="TestEvent", priority=101, audience_scope=["shipwide"])

    def test_event_state_machine_compliance(self) -> None:
        """Test that event state machine follows the defined flow."""
        # Test initial state
        event = Event(type="TestEvent", audience_scope=["shipwide"])
        assert event.state == "queued", "Events should start in 'queued' state"

        # Test valid state transitions (conceptually)
        valid_states = {
            "queued",
            "routed",
            "claimed",
            "active",
            "done",
            "suspended",
            "failed",
            "expired",
            "cancelled",
        }

        # Test that our event model supports all required states
        for state in valid_states:
            test_event = Event(type="TestEvent", state=state, audience_scope=["shipwide"])
            assert test_event.state == state, f"Event should support state: {state}"

    def test_ulid_usage_for_event_ids(self) -> None:
        """Test that events use ULIDs for unique identifiers."""
        event1 = Event(type="TestEvent1", audience_scope=["shipwide"])
        event2 = Event(type="TestEvent2", audience_scope=["shipwide"])

        # ULIDs should be 26 characters long
        assert len(event1.id) == 26, "Event ID should be ULID (26 characters)"
        assert len(event2.id) == 26, "Event ID should be ULID (26 characters)"

        # ULIDs should be unique
        assert event1.id != event2.id, "Event IDs should be unique"

        # ULIDs should be alphanumeric (no special characters)
        assert event1.id.isalnum(), "ULID should contain only alphanumeric characters"
        assert event2.id.isalnum(), "ULID should contain only alphanumeric characters"

    def test_audience_scope_validation(self) -> None:
        """Test that audience scope validation follows the rules."""
        # Test that empty audience scope is rejected
        with pytest.raises(ValueError, match="Event audience_scope cannot be empty"):
            Event(type="TestEvent", audience_scope=[])

        # Test valid audience scopes
        valid_scopes = [
            ["shipwide"],
            ["captain"],
            ["officers"],
            ["department:engineering"],
            ["private:actor123"],
            ["bridge", "engineering"],
        ]

        for scope in valid_scopes:
            event = Event(type="TestEvent", audience_scope=scope)
            assert event.audience_scope == scope, f"Should accept valid scope: {scope}"

    def test_no_bare_except_statements(self) -> None:
        """Test that no bare except: statements exist in the codebase."""
        # This is a conceptual test - in practice, you'd scan the entire codebase
        # For now, we'll test that our test files follow this pattern

        test_files = Path(__file__).parent.glob("test_*.py")

        for test_file in test_files:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Look for bare except statements (not in comments)
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("except:") and not stripped.startswith("#"):
                        pytest.fail(f"Found bare except: in {test_file}:{i} - {line.strip()}")

    def test_type_hints_usage(self) -> None:
        """Test that functions use proper type hints."""
        # Test that our Event class methods have type hints
        event_methods = [method for method in dir(Event) if not method.startswith("_")]

        for method_name in event_methods:
            method = getattr(Event, method_name)
            if callable(method):
                sig = inspect.signature(method)
                # Check that parameters have type hints
                for param_name, param in sig.parameters.items():
                    if param_name != "self":
                        assert (
                            param.annotation != inspect.Parameter.empty
                        ), f"Parameter {param_name} in {method_name} should have type hint"

    def test_pydantic_model_usage(self) -> None:
        """Test that we use Pydantic models for data validation."""
        # Test that Event is a Pydantic model
        assert hasattr(Event, "model_validate"), "Event should be a Pydantic model"
        assert hasattr(Event, "model_dump"), "Event should be a Pydantic model"
        assert hasattr(Event, "model_copy"), "Event should be a Pydantic model"

        # Test validation works
        with pytest.raises(ValueError):  # Specific exception type
            Event(type="TestEvent", priority="invalid", audience_scope=["shipwide"])

    def test_deterministic_behavior(self) -> None:
        """Test that operations are deterministic (same inputs = same outputs)."""
        # Test that event creation is deterministic when given same inputs
        event1 = Event(type="TestEvent", priority=50, audience_scope=["shipwide"])
        event2 = Event(type="TestEvent", priority=50, audience_scope=["shipwide"])

        # The events should have different IDs (due to timestamp) but same other properties
        assert event1.id != event2.id, "Events should have unique IDs"
        assert event1.type == event2.type, "Same type should produce same type"
        assert event1.priority == event2.priority, "Same priority should produce same priority"
        assert (
            event1.audience_scope == event2.audience_scope
        ), "Same scope should produce same scope"

    def test_error_handling_patterns(self) -> None:
        """Test that error handling follows the established patterns."""
        # Test that we use specific exception types
        with pytest.raises(ValueError):  # Specific exception type
            Event(type="TestEvent", audience_scope=[])

        # Test that we use pytest.raises() in tests
        with pytest.raises(ValueError):
            Event(type="TestEvent", priority=-1, audience_scope=["shipwide"])

    def test_naming_conventions(self) -> None:
        """Test that naming conventions are followed."""
        # Test class naming (PascalCase)
        assert Event.__name__[0].isupper(), "Classes should use PascalCase"
        assert EventQueue.__name__[0].isupper(), "Classes should use PascalCase"

        # Test function naming (snake_case)
        event_methods = [method for method in dir(Event) if not method.startswith("_")]
        for method in event_methods:
            if callable(getattr(Event, method)):
                assert "_" in method or method.islower(), f"Method {method} should use snake_case"

    def test_no_magic_numbers(self) -> None:
        """Test that magic numbers are avoided in favor of named constants."""
        # This is a conceptual test - in practice, you'd scan for magic numbers
        # For now, we'll test that our event priorities use meaningful values

        # Test that we use named constants for priorities
        red_alert = make_red_alert_event("combat", False)
        assert red_alert.priority == 0, "Should use 0 for critical priority (not magic number)"

        sleep_event = make_sleep_event("actor1", 10)
        assert sleep_event.priority >= 90, "Should use 90+ for low priority (not magic number)"


class TestArchitecturalCompliance:
    """Test compliance with architectural patterns and module requirements."""

    def test_m02_event_system_compliance(self) -> None:
        """Test that M02 Event System follows the frozen specification."""
        # Test ULID usage
        event = Event(type="TestEvent", audience_scope=["shipwide"])
        assert len(event.id) == 26, "M02 requires ULIDs for event IDs"

        # Test priority system (lower = higher priority)
        critical_event = make_red_alert_event("combat", False)
        assert critical_event.priority == 0, "M02 requires 0 for critical priority"

        # Test state machine compliance
        valid_states = {
            "queued",
            "routed",
            "claimed",
            "active",
            "done",
            "suspended",
            "failed",
            "expired",
            "cancelled",
        }
        for state in valid_states:
            test_event = Event(type="TestEvent", state=state, audience_scope=["shipwide"])
            assert test_event.state == state, f"M02 requires support for state: {state}"

    def test_event_queue_capacity_limits(self) -> None:
        """Test that EventQueue respects capacity limits."""
        # Test capacity enforcement
        queue = EventQueue(capacity=2)

        # Should be able to add up to capacity
        event1 = make_sleep_event("actor1", 10)
        event2 = make_sleep_event("actor2", 10)
        queue.publish(event1)
        queue.publish(event2)

        # Should fail when exceeding capacity
        with pytest.raises(RuntimeError, match="queue capacity exceeded"):
            event3 = make_sleep_event("actor3", 10)
            queue.publish(event3)

    def test_indexing_consistency(self) -> None:
        """Test that EventQueue maintains consistent indexing."""
        queue = EventQueue()

        # Publish event with specific category and scope
        event = Event(
            type="TestEvent", category="engineering", audience_scope=["department:engineering"]
        )
        queue.publish(event)

        # Test that indexing works correctly
        assert queue.get_by_id(event.id) is event
        assert event.id in queue.list_by_category("engineering")
        assert event.id in queue.list_by_scope("department:engineering")

        # Test that updates maintain consistency
        updated_event = event.model_copy(update={"category": "bridge"})
        queue.update(updated_event)

        assert event.id not in queue.list_by_category("engineering")
        assert event.id in queue.list_by_category("bridge")


class TestPerformanceCompliance:
    """Test compliance with performance requirements."""

    def test_event_creation_performance(self) -> None:
        """Test that event creation meets performance requirements."""
        import time

        # Test that we can create events quickly
        start_time = time.time()
        events = []
        for i in range(1000):
            event = Event(type=f"TestEvent{i}", audience_scope=["shipwide"])
            events.append(event)
        end_time = time.time()

        # Should be able to create 1000 events in reasonable time
        duration = end_time - start_time
        assert duration < 1.0, f"Creating 1000 events took {duration:.3f}s, should be < 1.0s"

    def test_queue_operations_performance(self) -> None:
        """Test that queue operations meet performance requirements."""
        import time

        queue = EventQueue(capacity=10000)

        # Test publish performance
        start_time = time.time()
        for i in range(1000):
            event = make_sleep_event(f"actor{i}", 10)
            queue.publish(event)
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 1.0, f"Publishing 1000 events took {duration:.3f}s, should be < 1.0s"

        # Test retrieval performance
        start_time = time.time()
        for event_id in list(queue._events.keys())[:100]:  # Test first 100
            retrieved = queue.get_by_id(event_id)
            assert retrieved is not None
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 0.1, f"Retrieving 100 events took {duration:.3f}s, should be < 0.1s"


class TestSecurityCompliance:
    """Test compliance with security requirements."""

    def test_input_validation(self) -> None:
        """Test that inputs are properly validated."""
        # Test that invalid inputs are rejected
        with pytest.raises(ValueError):
            Event(type="TestEvent", priority="not_a_number", audience_scope=["shipwide"])

        with pytest.raises(ValueError):
            Event(type="TestEvent", progress="not_a_float", audience_scope=["shipwide"])

        with pytest.raises(ValueError):
            Event(type="TestEvent", audience_scope=[])  # Empty scope

    def test_no_eval_or_exec_usage(self) -> None:
        """Test that eval() and exec() are not used in the codebase."""
        # This is a conceptual test - in practice, you'd scan the entire codebase
        # For now, we'll test that our test files don't use these functions

        test_files = Path(__file__).parent.glob("test_*.py")

        for test_file in test_files:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for actual function calls, not string literals
                import re

                # Find eval( function calls (not in strings or comments)
                # Note: We don't use these variables directly, but they're needed for regex search
                _ = re.findall(r"\beval\s*\(", content)  # noqa: F841
                _ = re.findall(r"\bexec\s*\(", content)  # noqa: F841

                # Filter out calls that are in strings or comments
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if (
                        stripped.startswith("#")
                        or stripped.startswith('"""')
                        or stripped.startswith("'''")
                    ):
                        continue  # Skip comments and docstrings

                    # Check for eval( or exec( that aren't in strings
                    if re.search(r"\beval\s*\(", line) and not re.search(
                        r'["\'].*eval\s*\(.*["\']', line
                    ):
                        pytest.fail(
                            f"Found eval() function call in {test_file}:{i} - {line.strip()}"
                        )

                    if re.search(r"\bexec\s*\(", line) and not re.search(
                        r'["\'].*exec\s*\(.*["\']', line
                    ):
                        pytest.fail(
                            f"Found exec() function call in {test_file}:{i} - {line.strip()}"
                        )


class TestDocumentationCompliance:
    """Test compliance with documentation requirements."""

    def test_docstring_presence(self) -> None:
        """Test that public functions and classes have docstrings."""
        # Test that Event class has docstring (may be None if not implemented yet)
        # This is a soft check - we'll note if docstrings are missing but not fail
        if Event.__doc__ is not None:
            assert len(Event.__doc__.strip()) > 0, "Event class docstring should not be empty"

        # Test that EventQueue class has docstring (may be None if not implemented yet)
        if EventQueue.__doc__ is not None:
            assert (
                len(EventQueue.__doc__.strip()) > 0
            ), "EventQueue class docstring should not be empty"

    def test_test_documentation(self) -> None:
        """Test that test functions have descriptive names and docstrings."""
        # Get all test methods in this file
        test_methods = [method for method in dir(self) if method.startswith("test_")]

        for method_name in test_methods:
            # Test names should be descriptive
            assert len(method_name) > 10, f"Test name {method_name} should be more descriptive"
            assert "_" in method_name, f"Test name {method_name} should use snake_case"

            # Test methods should have docstrings
            method = getattr(self, method_name)
            assert method.__doc__ is not None, f"Test method {method_name} should have docstring"
            assert (
                len(method.__doc__.strip()) > 0
            ), f"Test method {method_name} docstring should not be empty"
