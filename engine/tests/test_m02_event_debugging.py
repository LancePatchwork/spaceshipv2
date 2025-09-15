"""Tests for event debugging and error reporting with comprehensive information."""

from __future__ import annotations

import pytest

from engine.m02_events import Event


class TestEventDebugging:
    """Tests for event creation debugging and error reporting."""

    def test_empty_audience_scope_error_with_stack_trace(self) -> None:
        """Test that empty audience scope error includes stack trace information."""
        with pytest.raises(ValueError) as exc_info:
            # Simulate a buggy event creation from a factory function
            def buggy_event_factory():
                """Simulate a buggy factory that forgets to set audience_scope."""
                return Event(
                    type="buggy.event",
                    category="test",
                    priority=50,
                    # BUG: Missing audience_scope - this should cause an error
                )

            buggy_event_factory()

        error_message = str(exc_info.value)

        # Verify comprehensive error message
        assert "Event audience_scope cannot be empty" in error_message
        assert "will never be routed to any actors" in error_message
        assert "stuck in 'queued' state" in error_message
        assert "bug in event creation" in error_message

        # Verify debugging guidance
        assert "shipwide" in error_message
        assert "officers" in error_message
        assert "department:" in error_message
        assert "private:" in error_message
        assert "captain" in error_message
        assert "rank:" in error_message
        assert "crew:" in error_message

    def test_error_with_mock_buggy_system_event(self) -> None:
        """Test error reporting for a mock system event that forgets audience scope."""

        def mock_system_event_creator():
            """Simulate a system component that creates events incorrectly."""
            # This simulates a real bug where system events are created without audience
            return Event(
                type="system.maintenance",
                category="engineering",
                priority=30,
                issuer="system_automation",
                payload={"component": "life_support", "action": "routine_check"},
                # BUG: System forgot to set audience_scope
            )

        with pytest.raises(ValueError) as exc_info:
            mock_system_event_creator()

        error_message = str(exc_info.value)

        # The error should clearly indicate this is a system bug
        assert "bug in event creation" in error_message
        assert "will never be routed" in error_message

        # Should suggest appropriate scopes for system events
        assert "shipwide" in error_message  # System events often need shipwide scope

    def test_error_with_mock_crew_event_bug(self) -> None:
        """Test error reporting for crew events that forget audience scope."""

        def mock_crew_task_creator(crew_member_id: str):
            """Simulate crew task creation that forgets audience scope."""
            return Event(
                type="task.manual_repair",
                category="engineering",
                priority=40,
                issuer=crew_member_id,
                payload={"task": "repair_hull_breach", "location": "deck_3"},
                # BUG: Forgot to set audience_scope for crew task
            )

        with pytest.raises(ValueError) as exc_info:
            mock_crew_task_creator("crew_123")

        error_message = str(exc_info.value)

        # Should suggest crew-appropriate scopes
        assert "private:" in error_message  # For individual crew tasks
        assert "department:" in error_message  # For department-wide tasks
        assert "officers" in error_message  # For escalation

    def test_error_with_mock_alert_event_bug(self) -> None:
        """Test error reporting for alert events that forget audience scope."""

        def mock_alert_creator():
            """Simulate alert creation that forgets audience scope."""
            return Event(
                type="alert.environmental",
                category="alerts",
                priority=10,
                issuer="environmental_monitor",
                payload={"alert_type": "oxygen_low", "severity": "critical"},
                # BUG: Critical alert without audience scope!
            )

        with pytest.raises(ValueError) as exc_info:
            mock_alert_creator()

        error_message = str(exc_info.value)

        # Should emphasize the critical nature of alerts
        assert "will never be routed" in error_message
        assert "shipwide" in error_message  # Alerts typically need shipwide scope

    def test_error_includes_event_context_information(self) -> None:
        """Test that error includes context about the event being created."""

        def mock_contextual_event_creator():
            """Create an event with rich context to test error reporting."""
            return Event(
                type="navigation.course_correction",
                category="navigation",
                priority=25,
                issuer="nav_computer",
                payload={
                    "from_coords": [100, 200, 300],
                    "to_coords": [150, 250, 350],
                    "reason": "avoid_asteroid_field",
                },
                # BUG: Navigation event without audience scope
            )

        with pytest.raises(ValueError) as exc_info:
            mock_contextual_event_creator()

        error_message = str(exc_info.value)

        # Should suggest navigation-appropriate scopes
        assert "department:" in error_message
        assert "officers" in error_message

    def test_error_with_nested_function_calls(self) -> None:
        """Test error reporting when event creation happens deep in call stack."""

        def deep_nested_event_creation():
            """Simulate event creation deep in call stack."""

            def level_3():
                def level_2():
                    def level_1():
                        # This is where the actual bug occurs
                        return Event(
                            type="deep.nested.event",
                            category="test",
                            priority=50,
                            # BUG: Deep in call stack, forgot audience_scope
                        )

                    return level_1()

                return level_2()

            return level_3()

        with pytest.raises(ValueError) as exc_info:
            deep_nested_event_creation()

        error_message = str(exc_info.value)

        # Should still provide clear debugging information
        assert "Event audience_scope cannot be empty" in error_message
        assert "bug in event creation" in error_message

    def test_error_with_dynamic_event_creation(self) -> None:
        """Test error reporting for dynamically created events."""

        def dynamic_event_creator(event_type: str, category: str):
            """Simulate dynamic event creation that can be buggy."""
            # This simulates a system that creates events based on configuration
            return Event(
                type=event_type,
                category=category,
                priority=50,
                # BUG: Dynamic creation forgot audience_scope
            )

        with pytest.raises(ValueError) as exc_info:
            dynamic_event_creator("dynamic.test_event", "test_category")

        error_message = str(exc_info.value)

        # Should provide guidance for dynamic events
        assert "Event audience_scope cannot be empty" in error_message
        assert "shipwide" in error_message  # Safe default for dynamic events

    def test_error_message_completeness(self) -> None:
        """Test that error message contains all necessary debugging information."""

        with pytest.raises(ValueError) as exc_info:
            Event(type="completeness.test", audience_scope=[])

        error_message = str(exc_info.value)

        # Check for all essential debugging elements
        required_elements = [
            "Event audience_scope cannot be empty",
            "will never be routed to any actors",
            "stuck in 'queued' state",
            "bug in event creation",
            "Valid audience scopes include:",
            "shipwide",
            "officers",
            "captain",
            "department:",
            "private:",
            "rank:",
            "crew:",
            "Use 'shipwide' for events that should be visible to all actors",
            "or specify appropriate department/role scopes",
        ]

        for element in required_elements:
            assert element in error_message, f"Missing required element: {element}"

    def test_error_with_factory_pattern_bug(self) -> None:
        """Test error reporting for factory pattern that has bugs."""

        class BuggyEventFactory:
            """Simulate a factory class that has bugs."""

            @staticmethod
            def create_repair_event(system_id: str, severity: str):
                """Buggy repair event factory."""
                return Event(
                    type="task.repair",
                    category="engineering",
                    priority=40 if severity == "minor" else 20,
                    payload={"system_id": system_id, "severity": severity},
                    # BUG: Factory forgot to set audience_scope
                )

            @staticmethod
            def create_medical_event(patient_id: str):
                """Buggy medical event factory."""
                return Event(
                    type="medical.treatment",
                    category="medical",
                    priority=30,
                    payload={"patient_id": patient_id},
                    # BUG: Medical events need specific audience scope
                )

        # Test repair event bug
        with pytest.raises(ValueError) as exc_info:
            BuggyEventFactory.create_repair_event("life_support", "minor")

        error_message = str(exc_info.value)
        assert "Event audience_scope cannot be empty" in error_message
        assert "department:" in error_message  # Should suggest department scope

        # Test medical event bug
        with pytest.raises(ValueError) as exc_info:
            BuggyEventFactory.create_medical_event("patient_123")

        error_message = str(exc_info.value)
        assert "Event audience_scope cannot be empty" in error_message
        assert "private:" in error_message  # Medical events often need private scope

    def test_error_with_batch_event_creation_bug(self) -> None:
        """Test error reporting when batch event creation has bugs."""

        def create_batch_events():
            """Simulate batch event creation with bugs."""
            events = []
            for i in range(3):
                # Some events are created correctly, others have bugs
                if i == 1:  # This one has the bug
                    events.append(
                        Event(
                            type=f"batch.event_{i}",
                            category="test",
                            priority=50,
                            # BUG: This event in the batch forgot audience_scope
                        )
                    )
                else:
                    events.append(
                        Event(
                            type=f"batch.event_{i}",
                            category="test",
                            priority=50,
                            audience_scope=["shipwide"],  # This one is correct
                        )
                    )
            return events

        with pytest.raises(ValueError) as exc_info:
            create_batch_events()

        error_message = str(exc_info.value)
        assert "Event audience_scope cannot be empty" in error_message
        assert "bug in event creation" in error_message
