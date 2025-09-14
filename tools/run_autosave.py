from __future__ import annotations

import argparse
import random
import time
from typing import cast

from engine.lib.config import EngineConfig, Paths
from engine.m11_persist import JsonSaveStore
from engine.workers.autosave import AutoSaver
from engine.workers.snapshots import InMemorySnapshotBus, SnapshotPublisher


class DemoSolver:
    """Deterministic solver incrementing ``battery_kw`` by ``dt_s``."""

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        battery = cast(float, state.get("battery_kw", 0.0)) + dt_s
        return {"battery_kw": battery}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-s", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--prefix", default="autosave_")
    args = parser.parse_args()

    cfg = EngineConfig()
    bus = InMemorySnapshotBus()
    solver = DemoSolver()
    pub = SnapshotPublisher(solver, cfg, bus)
    store = JsonSaveStore(Paths())
    saver = AutoSaver(bus, store, prefix=args.prefix, limit=args.limit)

    try:
        while True:
            now_ms = int(time.time() * 1000)
            pub.step(now_ms)
            path = saver.run_once(now_ms)
            if path:
                print(f"saved {path}")
            time.sleep(args.interval_s)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
