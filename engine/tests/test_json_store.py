from __future__ import annotations

from pathlib import Path

import pytest

from engine.lib.config import Paths
from engine.lib.contracts import SNAPSHOT_SCHEMA, SRS_VERSION, Snapshot
from engine.m11_persist import JsonSaveStore


@pytest.fixture
def sample_snap() -> Snapshot:
    return {
        "meta": {
            "ts_ms": 1,
            "tick": 1,
            "schema": SNAPSHOT_SCHEMA,
            "version": SRS_VERSION,
        },
        "state": {"foo": "bar"},
    }


def test_save_and_load(tmp_path: Path, sample_snap: Snapshot) -> None:
    paths = Paths(saves_dir=str(tmp_path / "saves"))
    store = JsonSaveStore(paths)

    store.save(sample_snap, name="alpha")
    loaded = store.load("alpha")
    assert loaded == sample_snap


def test_invalid_name(tmp_path: Path, sample_snap: Snapshot) -> None:
    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))

    with pytest.raises(ValueError):
        store.save(sample_snap, name="bad/name")
    with pytest.raises(ValueError):
        store.load("bad name")


def test_missing_file(tmp_path: Path) -> None:
    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))
    with pytest.raises(FileNotFoundError):
        store.load("does_not_exist")
