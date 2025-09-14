from __future__ import annotations

from typing import cast

import pytest

from engine.lib.contracts import SNAPSHOT_SCHEMA, SRS_VERSION, SaveStore, Snapshot
from engine.m11_persist import safe_name
from ui.core.actions import load_snapshot, save_last_snapshot
from ui.core.contracts import SnapshotProvider


class FakeStore(SaveStore):
    def __init__(self) -> None:
        self.saved: dict[str, Snapshot] = {}

    def save(self, snap: Snapshot, *, name: str) -> str:
        safe_name(name)
        self.saved[name] = snap
        return f"/fake/{name}.json"

    def load(self, name: str) -> Snapshot:
        safe_name(name)
        if name not in self.saved:
            raise FileNotFoundError(name)
        return self.saved[name]


class FakeProvider(SnapshotProvider):
    def __init__(self, snap: Snapshot | None) -> None:
        self._snap = snap

    def get_latest(self) -> dict[str, object] | None:
        return cast(dict[str, object], self._snap) if self._snap is not None else None


@pytest.fixture
def sample_snap() -> Snapshot:
    return {
        "meta": {
            "ts_ms": 1,
            "tick": 1,
            "schema": SNAPSHOT_SCHEMA,
            "version": SRS_VERSION,
        },
        "state": {},
    }


def test_save_returns_path(sample_snap: Snapshot) -> None:
    store = FakeStore()
    provider = FakeProvider(sample_snap)
    path = save_last_snapshot(store, provider, "alpha")
    assert path == "/fake/alpha.json"
    assert store.saved["alpha"] == sample_snap


def test_load_unknown_raises() -> None:
    store = FakeStore()
    with pytest.raises(FileNotFoundError):
        load_snapshot(store, "missing")


def test_no_snapshot_raises() -> None:
    store = FakeStore()
    provider = FakeProvider(None)
    with pytest.raises(ValueError):
        save_last_snapshot(store, provider, "alpha")


def test_invalid_name_raises(sample_snap: Snapshot) -> None:
    store = FakeStore()
    provider = FakeProvider(sample_snap)
    with pytest.raises(ValueError):
        save_last_snapshot(store, provider, "bad/name")
    with pytest.raises(ValueError):
        load_snapshot(store, "bad name")
