from __future__ import annotations

from pathlib import Path

from engine.lib.config import Paths
from engine.lib.contracts import Snapshot, SnapshotSource
from engine.m11_persist import JsonSaveStore
from engine.workers.autosave import AutoSaver


class FakeSource(SnapshotSource):
    def __init__(self) -> None:
        self._tick = 0

    def get_latest(self) -> Snapshot | None:
        self._tick += 1
        return {
            "meta": {"ts_ms": 0, "tick": self._tick, "schema": "s", "version": "v"},
            "state": {},
        }


def test_autosave_rotates(tmp_path: Path) -> None:
    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))
    saver = AutoSaver(FakeSource(), store, limit=3)

    paths = []
    for _ in range(5):
        path = saver.run_once(0)
        assert path is not None
        paths.append(Path(path))

    files = sorted(p.name for p in tmp_path.glob("autosave_*.json"))
    assert files == ["autosave_0003.json", "autosave_0004.json", "autosave_0005.json"]
    assert paths[-1].name == "autosave_0005.json"


class EmptySource(SnapshotSource):
    def get_latest(self) -> Snapshot | None:
        return None


def test_autosave_no_snapshot(tmp_path: Path) -> None:
    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))
    saver = AutoSaver(EmptySource(), store)
    assert saver.run_once(0) is None
    assert list(tmp_path.glob("*.json")) == []
