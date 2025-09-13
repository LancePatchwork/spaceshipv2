from __future__ import annotations

import random
import time
from pathlib import Path
from typing import cast

import typer

from engine.lib.config import EngineConfig, Paths
from engine.lib.contracts import Snapshot
from engine.m11_persist import JsonSaveStore
from engine.workers.snapshots import InMemorySnapshotBus, SnapshotPublisher
from ui.core.provider import PollingSnapshotProvider
from ui.windows.dashboard_tui import DashboardTUI


class DemoSolver:
    """Produce sample data for the dashboard."""

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        power = cast(dict[str, float], state.get("power", {}))
        life = cast(dict[str, float], state.get("life", {}))
        env = cast(dict[str, float], state.get("env", {}))

        plant_output_kw = power.get("plant_output_kw", 0.0) + 1.0 * dt_s
        battery_kw = power.get("battery_kw", 50.0) + (plant_output_kw - 5.0) * dt_s
        battery_capacity_kw = power.get("battery_capacity_kw", 100.0)

        o2_pct = life.get("o2_pct", 21.0) + rng.random() * 0.1 - 0.05
        life_temp_c = life.get("life_temp_c", 22.0) + rng.random() * 0.1 - 0.05
        ship_temp_c = (
            env.get("ship_temp_c", 22.0) + (life_temp_c - env.get("ship_temp_c", 22.0)) * 0.1 * dt_s
        )

        return {
            "power": {
                "plant_output_kw": plant_output_kw,
                "battery_kw": battery_kw,
                "battery_capacity_kw": battery_capacity_kw,
            },
            "life": {"o2_pct": o2_pct, "life_temp_c": life_temp_c},
            "env": {"ship_temp_c": ship_temp_c},
        }


app = typer.Typer()


@app.command()
def main(
    steps: int = typer.Option(10, "--steps", help="Number of steps to run"),
    save: Path | None = typer.Option(None, "--save", help="Optional snapshot save path"),
) -> None:
    cfg = EngineConfig(tick_hz=2)
    bus = InMemorySnapshotBus()
    solver = DemoSolver()
    pub = SnapshotPublisher(solver, cfg, bus)

    snap: Snapshot | None = None
    for _ in range(steps):
        now_ms = int(time.time() * 1000)
        snap = pub.step(now_ms)
        time.sleep(0.5)

    if save is not None and snap is not None:
        store = JsonSaveStore(Paths(saves_dir=str(save.parent)))
        path = store.save(snap, name=save.stem)
        print(path)

    provider = PollingSnapshotProvider(bus)
    DashboardTUI(provider).run()


if __name__ == "__main__":
    typer.run(main)
