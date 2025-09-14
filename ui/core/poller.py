from __future__ import annotations

from typing import Mapping, cast

from PyQt6.QtCore import QObject, QTimer

from .binding import to_dashboard_vm
from .contracts import SnapshotProvider, Widget

WidgetRegistry = Mapping[str, Widget]


class SnapshotPoller(QObject):
    """Poll snapshots and push view-model slices to widgets."""

    def __init__(
        self,
        provider: SnapshotProvider,
        registry: WidgetRegistry,
        interval_ms: int = 500,
    ) -> None:
        super().__init__()
        self._provider = provider
        self._registry = registry
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._on_tick)

    def start(self) -> None:
        """Start polling for snapshots."""

        self._timer.start()

    def stop(self) -> None:
        """Stop polling for snapshots."""

        self._timer.stop()

    def _on_tick(self) -> None:
        snap = self._provider.get_latest()
        if snap is None:
            return

        vm = to_dashboard_vm(snap)
        for name, widget in self._registry.items():
            slice_vm = vm if name == "dashboard" else vm.get(name)
            if slice_vm is not None:
                widget.set_view(cast(dict[str, object], slice_vm))
