from __future__ import annotations

import json
import random
import time
from typing import cast

from engine.lib.config import EngineConfig
from engine.workers.snapshots import InMemorySnapshotBus, SnapshotPublisher


class DemoSolver:
    """Deterministic solver incrementing ``battery_kw`` by ``dt_s``."""

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        battery = cast(float, state.get("battery_kw", 0.0)) + dt_s
        return {"battery_kw": battery}


def main() -> None:
    cfg = EngineConfig(tick_hz=2)
    bus = InMemorySnapshotBus()
    solver = DemoSolver()
    pub = SnapshotPublisher(solver, cfg, bus)

    for _ in range(5):
        now_ms = int(time.time() * 1000)
        snap = pub.step(now_ms)
        print(json.dumps(snap, separators=(",", ":")))
        time.sleep(1 / cfg.tick_hz)


if __name__ == "__main__":
    main()
