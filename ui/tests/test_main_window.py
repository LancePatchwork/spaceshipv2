from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ui.core.app import create_app
from ui.core.registry import WidgetRegistry
from ui.windows.main_window import MainWindow


class DummyWidget(QWidget):
    pass


def test_main_window_adds_panels() -> None:
    create_app()  # ensure QApplication exists
    registry = WidgetRegistry()
    for name in ["Power", "Battery", "Life"]:
        registry.register(name, DummyWidget)

    window = MainWindow(registry)
    for name in ["Power", "Battery", "Life"]:
        window.show_panel(name)

    assert set(window._dock_widgets.keys()) == {"Power", "Battery", "Life"}
