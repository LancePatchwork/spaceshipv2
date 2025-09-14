from __future__ import annotations

from typing import Dict, cast

from engine.lib.contracts import SaveStore, Snapshot
from engine.m11_persist import safe_name

from .contracts import SnapshotProvider


def save_last_snapshot(store: SaveStore, provider: SnapshotProvider, name: str) -> str:
    """Persist the most recent snapshot using *store* under *name*.

    ``provider`` supplies the latest snapshot (M07) while ``store`` performs the
    atomic JSON save (M11). ``name`` must satisfy :func:`safe_name` rules.

    Returns the path written to or raises ``ValueError`` if no snapshot is
    available or the name is invalid.
    """

    safe_name(name)
    snap = provider.get_latest()
    if snap is None:
        raise ValueError("no snapshot available")
    return store.save(cast(Snapshot, snap), name=name)


def load_snapshot(store: SaveStore, name: str) -> Dict[str, object]:
    """Load and return a previously saved snapshot from *store*.

    ``name`` must satisfy :func:`safe_name` rules. ``FileNotFoundError`` is
    propagated if the snapshot does not exist.
    """

    safe_name(name)
    return cast(Dict[str, object], store.load(name))
