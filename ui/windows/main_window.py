from __future__ import annotations

from engine.lib.contracts import SaveStore
from ui.core.actions import load_snapshot, save_last_snapshot
from ui.core.contracts import SnapshotProvider


class MainWindow:
    """Text-based main window stub with file menu actions."""

    def __init__(self, store: SaveStore, provider: SnapshotProvider) -> None:
        self._store = store
        self._provider = provider

    def save_last_snapshot_action(self) -> None:
        name = input("Save snapshot as: ")
        try:
            path = save_last_snapshot(self._store, self._provider, name)
        except Exception as exc:  # pragma: no cover - UI feedback
            print(f"Save failed: {exc}")
            return
        print(f"Snapshot saved to {path}")

    def load_snapshot_action(self) -> None:
        name = input("Load snapshot name: ")
        try:
            snap = load_snapshot(self._store, name)
        except Exception as exc:  # pragma: no cover - UI feedback
            print(f"Load failed: {exc}")
            return
        print(f"Loaded snapshot: {name} (tick={snap.get('meta', {}).get('tick')})")
