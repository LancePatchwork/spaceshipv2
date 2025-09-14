"""Simple power status panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ui.core.contracts import PowerVM, Widget

if TYPE_CHECKING:

    class QWidget:  # pragma: no cover - typing stub
        def setLayout(self, layout: "QVBoxLayout") -> None: ...

    class QLabel(QWidget):  # pragma: no cover - typing stub
        def __init__(self, text: str = "") -> None: ...

        def setText(self, text: str) -> None: ...

        def text(self) -> str: ...

    class QVBoxLayout:  # pragma: no cover - typing stub
        def addWidget(self, widget: QWidget) -> None: ...

else:  # pragma: no cover
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-not-found]


class PowerPanel(QWidget):
    """Display current and maximum power plant output."""

    def __init__(self) -> None:
        super().__init__()
        self._output = QLabel("Output: 0.0 kW")
        self._capacity = QLabel("Capacity: 0.0 kW")
        layout = QVBoxLayout()
        layout.addWidget(self._output)
        layout.addWidget(self._capacity)
        self.setLayout(layout)

    def name(self) -> str:
        return "Power"

    def set_view(self, vm: PowerVM) -> None:
        self._output.setText(f"Output: {vm['plant_kw']:.1f} kW")
        self._capacity.setText(f"Capacity: {vm['plant_max_kw']:.1f} kW")


def build() -> Widget:
    """Factory used by the registry."""
    from typing import cast

    return cast(Widget, PowerPanel())
