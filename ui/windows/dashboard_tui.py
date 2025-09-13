from __future__ import annotations

from typing import cast

from textual.app import App, ComposeResult
from textual.widgets import Static

from ui.core.provider import PollingSnapshotProvider


class DashboardTUI(App[None]):
    """Minimal dashboard displaying key snapshot fields."""

    def __init__(self, provider: PollingSnapshotProvider) -> None:
        super().__init__()
        self._provider = provider
        self._status = Static("Waiting for data...")
        self._plant = Static()
        self._battery = Static()
        self._o2 = Static()
        self._life_temp = Static()
        self._ship_temp = Static()
        self._tick = Static()

    def compose(self) -> ComposeResult:
        yield self._status
        yield self._plant
        yield self._battery
        yield self._o2
        yield self._life_temp
        yield self._ship_temp
        yield self._tick

    def on_mount(self) -> None:
        self.set_interval(self._provider.interval_ms / 1000, self._refresh)

    def _refresh(self) -> None:
        snap = self._provider.get_latest()
        if snap is None:
            self._status.update("Waiting for data...")
            for widget in (
                self._plant,
                self._battery,
                self._o2,
                self._life_temp,
                self._ship_temp,
                self._tick,
            ):
                widget.update("")
            return

        self._status.update("")
        state = snap["state"]
        power = cast(dict[str, float], state.get("power", {}))
        life = cast(dict[str, float], state.get("life", {}))
        env = cast(dict[str, float], state.get("env", {}))

        self._plant.update(f"Plant Output: {power.get('plant_output_kw', 0.0):.1f} kW")
        self._battery.update(
            "Battery: "
            f"{power.get('battery_kw', 0.0):.1f} / "
            f"{power.get('battery_capacity_kw', 0.0):.1f} kW"
        )
        self._o2.update(f"O2: {life.get('o2_pct', 0.0):.1f}%")
        self._life_temp.update(f"Life Temp: {life.get('life_temp_c', 0.0):.1f} °C")
        self._ship_temp.update(f"Ship Temp: {env.get('ship_temp_c', 0.0):.1f} °C")
        self._tick.update(f"Tick: {snap['meta']['tick']}")
