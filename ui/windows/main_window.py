from __future__ import annotations

from typing import Mapping

from PyQt6.QtWidgets import QAction, QMainWindow

from ui.core.contracts import Widget
from ui.core.poller import SnapshotPoller
from ui.core.provider import PollingSnapshotProvider, SnapshotProviderAdapter


class MainWindow(QMainWindow):
    """Top-level window wiring the snapshot poller."""

    def __init__(self, provider: PollingSnapshotProvider, registry: Mapping[str, Widget]) -> None:
        super().__init__()
        adapter = SnapshotProviderAdapter(provider)
        self._poller = SnapshotPoller(adapter, registry)

        data_menu = self.menuBar().addMenu("Data")
        start_action = QAction("Start Polling", self)
        stop_action = QAction("Stop Polling", self)
        start_action.triggered.connect(self._poller.start)
        stop_action.triggered.connect(self._poller.stop)
        data_menu.addAction(start_action)
        data_menu.addAction(stop_action)
