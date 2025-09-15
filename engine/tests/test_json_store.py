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


def test_invalid_snapshot_format(tmp_path: Path) -> None:
    """Test loading invalid snapshot format to cover line 62."""
    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))

    # Create a file with invalid JSON structure
    invalid_file = tmp_path / "invalid.json"
    with invalid_file.open("w") as f:
        f.write('{"invalid": "structure"}')  # Missing "meta" and "state"

    with pytest.raises(ValueError, match="invalid snapshot"):
        store.load("invalid")


def test_save_cleanup_on_error(tmp_path: Path, sample_snap: Snapshot) -> None:
    """Test that temporary files are cleaned up on save error (line 54)."""
    from unittest.mock import patch

    store = JsonSaveStore(Paths(saves_dir=str(tmp_path)))

    # Mock os.replace to raise an exception, forcing cleanup path
    with patch("os.replace", side_effect=OSError("Mock error")):
        with pytest.raises(OSError):
            store.save(sample_snap, name="test")

    # Verify no temporary files are left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0, "Temporary files should be cleaned up"
