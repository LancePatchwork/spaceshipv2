from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ui.core.app import create_app
from ui.core.registry import register
from ui.windows.main_window import MainWindow


class DummyWidget(QWidget):
    def set_view(self, vm: dict[str, object]) -> None:
        pass

    def name(self) -> str:
        return "Dummy"


def test_main_window_adds_panels() -> None:
    create_app()  # ensure QApplication exists

    # Register test widgets
    for name in ["Power", "Battery", "Life"]:
        register(name.lower(), lambda: DummyWidget())

    window = MainWindow()
    for name in ["Power", "Battery", "Life"]:
        window.show_panel(name)

    assert set(window._dock_widgets.keys()) == {"Power", "Battery", "Life"}


def test_main_window_add_panel_early_return() -> None:
    """Test add_panel early return to cover line 31."""
    create_app()  # ensure QApplication exists

    window = MainWindow()
    widget = DummyWidget()

    # Add panel first time
    window.add_panel("TestPanel", widget)
    assert "TestPanel" in window._dock_widgets

    # Try to add same panel again - should return early
    window.add_panel("TestPanel", widget)
    # Should still have only one panel
    assert len(window._dock_widgets) == 1
