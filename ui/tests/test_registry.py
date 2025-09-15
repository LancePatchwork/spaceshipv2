from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ui.core.registry import build, ids, register


class DummyWidget(QWidget):
    def set_view(self, vm: dict[str, object]) -> None:
        pass

    def name(self) -> str:
        return "Dummy"


def test_registry_creates_registered_widget() -> None:
    # Register a test widget
    register("dummy", lambda: DummyWidget())

    # Test that we can build it
    widget = build("dummy")
    assert isinstance(widget, DummyWidget)

    # Test that it's in the ids list
    assert "dummy" in ids()

    # Clean up - remove the test registration
    # Note: The current registry doesn't have an unregister function
    # This is a limitation of the current design
