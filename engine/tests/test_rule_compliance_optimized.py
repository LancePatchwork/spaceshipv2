"""Optimized rule compliance tests using hash-based caching.

This demonstrates how to use the hash cache plugin to make tests
only run when relevant files have changed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine.m02_events import Event, EventQueue
from engine.m02_events.factories import make_red_alert_event, make_sleep_event

# Import the hash cache decorators
from pytest_hash_cache import hash_cache_files, hash_cache_glob


class TestOptimizedRuleCompliance:
    """Optimized rule compliance tests with hash caching."""

    @hash_cache_glob("**/*.py", "engine/")
    def test_no_print_statements_in_engine_code(self) -> None:
        """Test that no print() statements exist in engine code."""
        engine_files = Path("engine/").glob("**/*.py")

        for file_path in engine_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Skip comments and docstrings
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue

                    # Check for print statements
                    if "print(" in line and not re.search(r'["\'].*print\s*\(.*["\']', line):
                        pytest.fail(f"Found print() statement in {file_path}:{i} - {line.strip()}")

    @hash_cache_glob("**/*.py", "ui/")
    def test_no_print_statements_in_ui_code(self) -> None:
        """Test that no print() statements exist in UI code."""
        ui_files = Path("ui/").glob("**/*.py")

        for file_path in ui_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Skip comments and docstrings
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue

                    # Check for print statements
                    if "print(" in line and not re.search(r'["\'].*print\s*\(.*["\']', line):
                        pytest.fail(f"Found print() statement in {file_path}:{i} - {line.strip()}")

    @hash_cache_files("engine/m02_events/models.py", "engine/m02_events/queue.py")
    def test_event_system_compliance(self) -> None:
        """Test that event system follows all rules."""
        # Test ULID usage
        event = Event(type="TestEvent", audience_scope=["shipwide"])
        assert len(event.id) == 26, "Event ID should be ULID (26 characters)"

        # Test priority system
        critical_event = make_red_alert_event("combat", False)
        assert critical_event.priority == 0, "Red alert should have priority 0"

        # Test state machine
        assert event.state == "queued", "Events should start in 'queued' state"

    @hash_cache_glob("**/*.py", "engine/m02_events/")
    def test_no_bare_except_in_event_system(self) -> None:
        """Test that no bare except statements exist in event system."""
        event_files = Path("engine/m02_events/").glob("**/*.py")

        for file_path in event_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("except:") and not stripped.startswith("#"):
                        pytest.fail(f"Found bare except: in {file_path}:{i} - {line.strip()}")

    @hash_cache_glob("**/*.py", "ui/")
    def test_no_hardcoded_colors_in_ui(self) -> None:
        """Test that UI code doesn't have hardcoded colors."""
        ui_files = Path("ui/").glob("**/*.py")

        color_patterns = [
            r"#[0-9a-fA-F]{6}",  # Hex colors
            r"#[0-9a-fA-F]{3}",  # Short hex colors
            r"rgb\s*\(",  # RGB colors
            r"rgba\s*\(",  # RGBA colors
            r"QColor\s*\(",  # Qt color constructors
        ]

        for file_path in ui_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Skip comments and docstrings
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue

                    # Check for color patterns
                    for pattern in color_patterns:
                        if re.search(pattern, line) and not re.search(
                            r'["\'].*' + pattern + r'.*["\']', line
                        ):
                            pytest.fail(
                                f"Found hardcoded color in {file_path}:{i} - {line.strip()}"
                            )

    @hash_cache_files("engine/m02_events/models.py")
    def test_event_validation_rules(self) -> None:
        """Test that event validation follows all rules."""
        # Test audience scope validation
        with pytest.raises(ValueError, match="Event audience_scope cannot be empty"):
            Event(type="TestEvent", audience_scope=[])

        # Test priority validation
        with pytest.raises(ValueError):
            Event(type="TestEvent", priority=-1, audience_scope=["shipwide"])

        with pytest.raises(ValueError):
            Event(type="TestEvent", priority=101, audience_scope=["shipwide"])

    @hash_cache_glob("**/*.py", "engine/")
    def test_no_eval_or_exec_in_engine(self) -> None:
        """Test that eval() and exec() are not used in engine code."""
        engine_files = Path("engine/").glob("**/*.py")

        for file_path in engine_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Skip comments and docstrings
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue

                    # Check for eval() or exec()
                    if re.search(r"\beval\s*\(", line) and not re.search(
                        r'["\'].*eval\s*\(.*["\']', line
                    ):
                        pytest.fail(f"Found eval() in {file_path}:{i} - {line.strip()}")

                    if re.search(r"\bexec\s*\(", line) and not re.search(
                        r'["\'].*exec\s*\(.*["\']', line
                    ):
                        pytest.fail(f"Found exec() in {file_path}:{i} - {line.strip()}")


class TestPerformanceOptimized:
    """Performance tests that only run when relevant files change."""

    @hash_cache_files("engine/m02_events/models.py", "engine/m02_events/queue.py")
    def test_event_creation_performance(self) -> None:
        """Test that event creation meets performance requirements."""
        import time

        start_time = time.time()
        events = []
        for i in range(1000):
            event = Event(type=f"TestEvent{i}", audience_scope=["shipwide"])
            events.append(event)
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 1.0, f"Creating 1000 events took {duration:.3f}s, should be < 1.0s"

    @hash_cache_files("engine/m02_events/queue.py")
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
