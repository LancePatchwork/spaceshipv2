from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ui.core.registry import WidgetRegistry


class DummyWidget(QWidget):
    pass


def test_registry_creates_registered_widget() -> None:
    registry = WidgetRegistry()
    registry.register("dummy", DummyWidget)

    widget = registry.create("dummy")
    assert isinstance(widget, DummyWidget)
