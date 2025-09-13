from __future__ import annotations

import random
from typing import cast

from engine.lib.config import EngineConfig
from engine.workers.snapshots import InMemorySnapshotBus, SnapshotPublisher


class DummySolver:
    """Simple solver adding ``dt_s`` to ``battery_kw`` each tick."""

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        battery = cast(float, state.get("battery_kw", 0.0)) + dt_s
        return {"battery_kw": battery}


def test_step_increments_and_publishes() -> None:
    cfg = EngineConfig(tick_hz=2)
    bus = InMemorySnapshotBus()
    solver = DummySolver()
    pub = SnapshotPublisher(solver, cfg, bus)

    snap1 = pub.step(0)
    assert snap1["meta"]["tick"] == 1
    assert snap1["state"]["battery_kw"] == 0.5

    snap2 = pub.step(500)
    assert snap2["meta"]["tick"] == 2
    assert snap2["state"]["battery_kw"] == 1.0

    assert bus.get_latest() == snap2
