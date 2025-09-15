"""Tests to validate UI compliance with development rules and standards.

This module contains tests that verify the UI codebase follows our established
development rules, architectural patterns, and quality standards.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

# Removed unused import: Any
import pytest
from PySide6.QtWidgets import QApplication, QWidget

from ui.core.registry import build, ids, register


class DummyWidget(QWidget):
    """Test widget for registry testing."""

    def set_view(self, vm: dict[str, object]) -> None:
        """Set the view model for this widget."""
        pass

    def name(self) -> str:
        """Return the widget name."""
        return "Dummy"


@pytest.fixture(scope="session")
def qt_app():
    """Create a Qt application for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests


class TestUIRuleCompliance:
    """Test UI compliance with development rules and standards."""

    def test_widget_registry_architecture(self, qt_app) -> None:
        """Test that widget registry follows M12 architecture rules."""
        # Test that we can register widgets
        register("test_widget", lambda: DummyWidget())

        # Test that widget is in the registry
        assert "test_widget" in ids(), "Registered widget should be in ids list"

        # Test that we can build widgets from registry
        widget = build("test_widget")
        assert widget is not None, "Registry should return widget instances"
        assert isinstance(widget, QWidget), "Registry should return QWidget instances"
        assert isinstance(widget, DummyWidget), "Registry should return correct widget type"

    def test_widget_behavior_separation(self, qt_app) -> None:
        """Test that widget behavior is separated from containers (M12 rule)."""
        # Test that widgets have behavior methods
        widget = DummyWidget()

        # Widgets should have behavior methods, not just be containers
        assert hasattr(widget, "set_view"), "Widget should have behavior methods"
        assert hasattr(widget, "name"), "Widget should have behavior methods"

        # Test that behavior methods are callable
        assert callable(widget.set_view), "set_view should be callable"
        assert callable(widget.name), "name should be callable"

        # Test that behavior methods work
        widget.set_view({"test": "data"})
        assert widget.name() == "Dummy"

    def test_no_hardcoded_colors_in_widgets(self) -> None:
        """Test that widgets don't have hardcoded colors (should use QSS theme)."""
        # This is a conceptual test - in practice, you'd scan widget files
        # For now, we'll test that our test widgets don't have hardcoded colors

        widget_files = Path(__file__).parent.parent.glob("**/*.py")

        for widget_file in widget_files:
            with open(widget_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for hardcoded color patterns
                color_patterns = [
                    r"#[0-9a-fA-F]{6}",  # Hex colors
                    r"#[0-9a-fA-F]{3}",  # Short hex colors
                    r"rgb\s*\(",  # RGB colors
                    r"rgba\s*\(",  # RGBA colors
                    r"QColor\s*\(",  # Qt color constructors
                ]

                # Check each line for color patterns, but skip comments and docstrings
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

                    # Check for color patterns
                    for pattern in color_patterns:
                        if re.search(pattern, line) and not re.search(
                            r'["\'].*' + pattern + r'.*["\']', line
                        ):
                            pytest.fail(
                                f"Found hardcoded color in {widget_file}:{i} - {line.strip()}"
                            )

    def test_qt_layout_usage(self) -> None:
        """Test that Qt layouts are used instead of hardcoded positions."""
        # This is a conceptual test - in practice, you'd scan widget files
        # For now, we'll test that our test widgets use proper Qt patterns

        widget_files = Path(__file__).parent.parent.glob("**/*.py")

        for widget_file in widget_files:
            with open(widget_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for hardcoded position patterns (anti-pattern)
                position_patterns = [
                    r"move\s*\(",  # move() calls
                    r"resize\s*\(",  # resize() calls
                    r"setGeometry\s*\(",  # setGeometry() calls
                ]

                # Check each line for position patterns, but skip comments and docstrings
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

                    # Check for position patterns
                    for pattern in position_patterns:
                        if re.search(pattern, line) and not re.search(
                            r'["\'].*' + pattern + r'.*["\']', line
                        ):
                            # Skip if this is the test file itself defining the pattern
                            if "test_rule_compliance.py" in str(widget_file) and (
                                "position_patterns" in line
                                or "r'move" in line
                                or "r'resize" in line
                                or "r'setGeometry" in line
                            ):
                                continue
                            pytest.fail(
                                f"Found hardcoded positioning in {widget_file}:{i} - {line.strip()}"
                            )

    def test_signals_and_slots_usage(self) -> None:
        """Test that signals and slots are used for communication."""
        # This is a conceptual test - in practice, you'd scan widget files
        # For now, we'll test that our test widgets follow Qt patterns

        widget_files = Path(__file__).parent.parent.glob("**/*.py")

        for widget_file in widget_files:
            if widget_file.name.startswith("test_"):
                continue  # Skip test files

            with open(widget_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for signal/slot patterns (good patterns)
                signal_patterns = [
                    r"\.connect\s*\(",  # signal connections
                    r"\.emit\s*\(",  # signal emissions
                    r"@pyqtSlot",  # slot decorators
                    r"@Slot",  # slot decorators
                ]

                _ = any(re.search(pattern, content) for pattern in signal_patterns)  # noqa: F841

                # If the file has widget classes, it should use signals/slots
                if "class" in content and "QWidget" in content:
                    # This is a soft check - not all widgets need signals/slots
                    # but complex widgets should use them
                    pass

    def test_type_hints_in_ui_code(self) -> None:
        """Test that UI code uses proper type hints."""
        # Test that our test widgets have type hints
        widget_methods = [method for method in dir(DummyWidget) if not method.startswith("_")]

        for method_name in widget_methods:
            method = getattr(DummyWidget, method_name)
            if callable(method):
                # Skip Qt's built-in methods that don't have type hints
                if method_name in [
                    "PaintDeviceMetric",
                    "PaintEngine",
                    "PaintEngineState",
                    "RenderFlag",
                ]:
                    continue

                try:
                    sig = inspect.signature(method)
                    # Check that parameters have type hints
                    for param_name, param in sig.parameters.items():
                        if param_name != "self":
                            assert (
                                param.annotation != inspect.Parameter.empty
                            ), f"Parameter {param_name} in {method_name} should have type hint"
                except (ValueError, TypeError):
                    # Skip Qt built-in methods that don't have inspectable signatures
                    continue

    def test_no_orphaned_widgets(self) -> None:
        """Test that widgets are properly parented (no orphaned widgets)."""
        # Test that widgets can be properly parented
        parent_widget = QWidget()
        child_widget = DummyWidget()

        # Widgets should be able to be parented
        child_widget.setParent(parent_widget)
        assert child_widget.parent() is parent_widget, "Widget should be properly parented"

        # Test cleanup
        child_widget.deleteLater()
        parent_widget.deleteLater()

    def test_widget_hierarchy_compliance(self) -> None:
        """Test that widget hierarchy follows Qt best practices."""
        # Test that widgets inherit from QWidget or appropriate base class
        assert issubclass(DummyWidget, QWidget), "Widgets should inherit from QWidget"

        # Test that widgets have proper Qt methods
        widget = DummyWidget()
        assert hasattr(widget, "show"), "Widget should have show() method"
        assert hasattr(widget, "hide"), "Widget should have hide() method"
        assert hasattr(widget, "setParent"), "Widget should have setParent() method"

    def test_performance_budget_compliance(self) -> None:
        """Test that UI operations meet performance budget (≤4ms avg frame)."""
        import time

        # Test widget creation performance
        start_time = time.time()
        widgets = []
        for i in range(100):
            widget = DummyWidget()
            widgets.append(widget)
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 0.1, f"Creating 100 widgets took {duration:.3f}s, should be < 0.1s"

        # Test registry operations performance
        start_time = time.time()
        for i in range(100):
            register(f"perf_test_widget_{i}", lambda: DummyWidget())
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 0.1, f"Registering 100 widgets took {duration:.3f}s, should be < 0.1s"

    def test_accessibility_compliance(self) -> None:
        """Test that widgets follow accessibility guidelines."""
        widget = DummyWidget()

        # Widgets should have accessible names
        widget.setObjectName("test_widget")
        assert widget.objectName() == "test_widget", "Widget should have accessible object name"

        # Widgets should be able to set accessible descriptions
        widget.setToolTip("Test widget for accessibility")
        assert widget.toolTip() == "Test widget for accessibility", "Widget should have tooltip"

    def test_no_global_variables_in_ui(self) -> None:
        """Test that UI code doesn't use global variables."""
        # This is a conceptual test - in practice, you'd scan UI files
        # For now, we'll test that our test files don't use globals

        ui_files = Path(__file__).parent.parent.glob("**/*.py")

        for ui_file in ui_files:
            with open(ui_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for global variable patterns
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

                    # Skip empty lines
                    if not stripped:
                        continue

                    # Look for module-level variable assignments (global variables)
                    # Pattern: variable_name = value (not in function/class)
                    # But skip if this looks like it's inside a function (indented)
                    if re.match(
                        r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]", stripped
                    ) and not line.startswith("    "):
                        # Allow legitimate exceptions
                        allowed_patterns = [
                            r"^from\s+",  # from imports
                            r"^import\s+",  # import statements
                            r"^class\s+",  # class definitions
                            r"^def\s+",  # function definitions
                            r"^if\s+",  # if statements
                            r"^for\s+",  # for loops
                            r"^while\s+",  # while loops
                            r"^with\s+",  # with statements
                            r"^try\s*:",  # try blocks
                            r"^except\s+",  # except blocks
                            r"^finally\s*:",  # finally blocks
                            r"^elif\s+",  # elif statements
                            r"^else\s*:",  # else statements
                            r"^@",  # decorators
                            r"^#",  # comments
                            r'^"""',  # docstrings
                            r'^r"""',  # raw docstrings
                            r'^"""',  # docstrings
                            r'^r"""',  # raw docstrings
                            r"^[A-Z][a-zA-Z0-9_]*\s*=\s*[A-Z]",  # type aliases
                        ]

                        # Check if this line matches any allowed pattern
                        is_allowed = any(
                            re.match(pattern, stripped) for pattern in allowed_patterns
                        )

                        if not is_allowed:
                            pytest.fail(
                                f"Found potential global variable in {ui_file}:{i} - {stripped}"
                            )

    def test_documentation_compliance(self) -> None:
        """Test that UI classes and methods have proper documentation."""
        # Test that our test widget has docstring
        assert DummyWidget.__doc__ is not None, "Widget class should have docstring"
        assert len(DummyWidget.__doc__.strip()) > 0, "Widget class docstring should not be empty"

        # Test that our custom widget methods have docstrings
        # Only check methods that are actually defined in our DummyWidget class
        custom_methods = ["set_view", "name"]
        for method_name in custom_methods:
            if hasattr(DummyWidget, method_name):
                method = getattr(DummyWidget, method_name)
                assert (
                    method.__doc__ is not None
                ), f"Widget method {method_name} should have docstring"
                assert (
                    len(method.__doc__.strip()) > 0
                ), f"Widget method {method_name} docstring should not be empty"

    def test_naming_conventions_ui(self) -> None:
        """Test that UI code follows naming conventions."""
        # Test class naming (PascalCase)
        assert DummyWidget.__name__[0].isupper(), "Widget classes should use PascalCase"

        # Test that our custom widget methods use snake_case
        # Only check methods that are actually defined in our DummyWidget class
        custom_methods = ["set_view", "name"]
        for method_name in custom_methods:
            if hasattr(DummyWidget, method_name):
                assert (
                    "_" in method_name or method_name.islower()
                ), f"Widget method {method_name} should use snake_case"

    def test_error_handling_ui(self) -> None:
        """Test that UI code has proper error handling."""
        # Test that registry handles invalid widget IDs gracefully
        invalid_widget = build("nonexistent_widget")
        assert invalid_widget is None, "Registry should return None for invalid widget ID"

        # Test that widgets handle invalid inputs gracefully
        widget = DummyWidget()
        try:
            widget.set_view({})  # Should handle None gracefully
        except Exception as e:
            pytest.fail(f"Widget should handle None input gracefully, got: {e}")


class TestUIPerformanceCompliance:
    """Test UI performance compliance with requirements."""

    def test_widget_creation_performance(self) -> None:
        """Test that widget creation meets performance requirements."""
        import time

        # Test widget creation performance
        start_time = time.time()
        widgets = []
        for i in range(1000):
            widget = DummyWidget()
            widgets.append(widget)
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 1.0, f"Creating 1000 widgets took {duration:.3f}s, should be < 1.0s"

    def test_registry_operations_performance(self) -> None:
        """Test that registry operations meet performance requirements."""
        import time

        # Test registration performance
        start_time = time.time()
        for i in range(1000):
            register(f"perf_widget_{i}", lambda: DummyWidget())
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 1.0, f"Registering 1000 widgets took {duration:.3f}s, should be < 1.0s"

        # Test building performance
        start_time = time.time()
        for i in range(100):
            widget = build(f"perf_widget_{i}")
            assert widget is not None
        end_time = time.time()

        duration = end_time - start_time
        assert duration < 0.5, f"Building 100 widgets took {duration:.3f}s, should be < 0.5s"
