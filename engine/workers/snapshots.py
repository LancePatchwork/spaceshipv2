from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from engine.lib.config import EngineConfig
from engine.lib.contracts import (
    SNAPSHOT_SCHEMA,
    SRS_VERSION,
    Snapshot,
    SnapshotSink,
    SnapshotSource,
    TickSolver,
)
from engine.lib.rng import seed_for


class InMemorySnapshotBus(SnapshotSink, SnapshotSource):
    """A minimal in-memory snapshot bus.

    Stores only the latest snapshot published to it.
    Thread safety is intentionally omitted for simplicity.
    """

    def __init__(self) -> None:
        self._latest: Optional[Snapshot] = None

    def publish(self, snap: Snapshot) -> None:
        self._latest = snap

    def get_latest(self) -> Optional[Snapshot]:
        return self._latest


@dataclass
class SnapshotPublisher:
    """Run a tick loop and publish snapshots to a bus."""

    solver: TickSolver
    cfg: EngineConfig
    bus: SnapshotSink
    tick_idx: int = 0
    state: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._dt_s = 1.0 / self.cfg.tick_hz
        self._rng = seed_for(self.cfg.save_seed, "publisher")
        # Initialize state via solver helper with dt=0
        self.state = self.solver.tick({}, 0.0, rng=self._rng)

    def step(self, now_ms: int) -> Snapshot:
        """Advance one tick and publish the resulting snapshot."""
        self.tick_idx += 1
        self.state = self.solver.tick(self.state, self._dt_s, rng=self._rng)
        snap: Snapshot = {
            "meta": {
                "ts_ms": now_ms,
                "tick": self.tick_idx,
                "schema": SNAPSHOT_SCHEMA,
                "version": SRS_VERSION,
            },
            "state": self.state,
        }
        self.bus.publish(snap)
        return snap
