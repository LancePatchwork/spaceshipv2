"""Simple life-support status panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ui.core.contracts import LifeVM, Widget

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


class LifePanel(QWidget):
    """Display life-support metrics."""

    def __init__(self) -> None:
        super().__init__()
        self._o2 = QLabel("O2: 0.0%")
        self._life_temp = QLabel("Life Temp: 0.0 °C")
        self._ship_temp = QLabel("Ship Temp: 0.0 °C")
        self._crew = QLabel("Crew Awake: 0")
        layout = QVBoxLayout()
        layout.addWidget(self._o2)
        layout.addWidget(self._life_temp)
        layout.addWidget(self._ship_temp)
        layout.addWidget(self._crew)
        self.setLayout(layout)

    def name(self) -> str:
        return "Life"

    def set_view(self, vm: LifeVM) -> None:
        self._o2.setText(f"O2: {vm['o2_pct']:.1f}%")
        self._life_temp.setText(f"Life Temp: {vm['life_temp_c']:.1f} °C")
        self._ship_temp.setText(f"Ship Temp: {vm['ship_temp_c']:.1f} °C")
        self._crew.setText(f"Crew Awake: {vm['crew_awake']}")


def build() -> Widget:
    """Factory used by the registry."""
    from typing import cast

    return cast(Widget, LifePanel())
