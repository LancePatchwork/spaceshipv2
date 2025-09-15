from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from ui.core.registry import build


class MainWindow(QMainWindow):
    """Top-level application window with dockable panels."""

    def __init__(self) -> None:
        super().__init__()
        self._dock_widgets: Dict[str, QDockWidget] = {}

        self.setWindowTitle("Starship Simulator")

        view_menu = self.menuBar().addMenu("View")
        self._panels_menu = view_menu.addMenu("Panels")

        for name in ["Power", "Battery", "Life"]:
            action = self._panels_menu.addAction(name)
            action.triggered.connect(lambda checked=False, n=name: self.show_panel(n))

    def add_panel(self, name: str, widget: QWidget) -> None:
        """Dock ``widget`` under ``name`` if not already present."""

        if name in self._dock_widgets:
            return
        dock = QDockWidget(name, self)
        dock.setWidget(widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._dock_widgets[name] = dock

    def show_panel(self, name: str) -> None:
        """Ensure the panel ``name`` is created and visible."""

        if name not in self._dock_widgets:
            widget = build(name.lower())
            if widget:
                self.add_panel(name, widget)
        if name in self._dock_widgets:
            dock = self._dock_widgets[name]
            dock.show()
            dock.raise_()
