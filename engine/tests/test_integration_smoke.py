from __future__ import annotations

import random
from pathlib import Path
from typing import cast

from engine.lib.config import EngineConfig, Paths
from engine.m01_srs import solver as srs_solver
from engine.m01_srs.types import SRSState
from engine.m11_persist import JsonSaveStore
from engine.workers.snapshots import InMemorySnapshotBus, SnapshotPublisher


class SRSSolverWrapper:
    """Adapter exposing ``tick`` from the SRS solver as a class."""

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        base: SRSState
        if not state:
            base = srs_solver.make_initial_state()
        else:
            base = cast(SRSState, state)
        return cast(dict[str, object], srs_solver.tick(base, dt_s, rng=rng))


def test_integration_smoke(tmp_path: Path) -> None:
    cfg = EngineConfig(tick_hz=2)
    bus = InMemorySnapshotBus()
    solver = SRSSolverWrapper()
    pub = SnapshotPublisher(solver, cfg, bus)

    snap = None
    for i in range(5):
        snap = pub.step(i * 100)

    assert snap is not None
    assert snap["meta"]["tick"] == 5
    assert bus.get_latest() == snap

    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))
    store.save(snap, name="final")
    loaded = store.load("final")
    assert loaded == snap
