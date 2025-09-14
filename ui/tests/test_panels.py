from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

from ui.core.contracts import BatteryVM, LifeVM, PowerVM
from ui.widgets.battery_panel import BatteryPanel
from ui.widgets.life_panel import LifePanel
from ui.widgets.power_panel import PowerPanel


@pytest.fixture(scope="module")
def app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_power_panel_updates_labels(app: QApplication) -> None:
    panel = PowerPanel()
    vm: PowerVM = {"plant_kw": 42.0, "plant_max_kw": 100.0}
    panel.set_view(vm)
    assert panel._output.text() == "Output: 42.0 kW"
    assert panel._capacity.text() == "Capacity: 100.0 kW"


def test_battery_panel_updates_labels(app: QApplication) -> None:
    panel = BatteryPanel()
    vm: BatteryVM = {"kw": 10.5, "capacity_kw": 50.25}
    panel.set_view(vm)
    assert panel._charge.text() == "Charge: 10.5 kW"
    assert panel._capacity.text() == "Capacity: 50.2 kW"


def test_life_panel_updates_labels(app: QApplication) -> None:
    panel = LifePanel()
    vm: LifeVM = {
        "o2_pct": 21.0,
        "life_temp_c": 22.25,
        "ship_temp_c": 20.75,
        "crew_awake": 4,
    }
    panel.set_view(vm)
    assert panel._o2.text() == "O2: 21.0%"
    assert panel._life_temp.text() == "Life Temp: 22.2 °C"
    assert panel._ship_temp.text() == "Ship Temp: 20.8 °C"
    assert panel._crew.text() == "Crew Awake: 4"
