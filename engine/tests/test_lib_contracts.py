from __future__ import annotations

from engine.lib.config import EngineConfig, Paths
from engine.lib.contracts import (
    SNAPSHOT_SCHEMA,
    SRS_VERSION,
    Snapshot,
    SnapshotSource,
)


def test_config_defaults() -> None:
    cfg = EngineConfig()
    paths = Paths()
    assert cfg.tick_hz == 2
    assert cfg.save_seed == 123
    assert paths.snapshots_dir.endswith("data/snapshots")
    assert paths.saves_dir.endswith("data/saves")


def test_minimal_snapshot_structure() -> None:
    snap: Snapshot = {
        "meta": {
            "ts_ms": 1,
            "tick": 0,
            "schema": SNAPSHOT_SCHEMA,
            "version": SRS_VERSION,
        },
        "state": {"power": {}, "life": {}, "env": {}},
    }
    assert snap["meta"]["schema"] == SNAPSHOT_SCHEMA
    assert {"power", "life", "env"} <= snap["state"].keys()


class InMemorySource:
    def __init__(self, snap: Snapshot | None = None) -> None:
        self._snap = snap

    def get_latest(self) -> Snapshot | None:
        return self._snap


def test_snapshot_source_protocol() -> None:
    src: SnapshotSource = InMemorySource()
    assert src.get_latest() is None
