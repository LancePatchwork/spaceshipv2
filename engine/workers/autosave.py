from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.lib.contracts import SnapshotSource
from engine.m11_persist import JsonSaveStore


@dataclass
class AutoSaver:
    """Persist snapshots to disk with rotation."""

    source: SnapshotSource
    store: JsonSaveStore
    prefix: str = "autosave_"
    limit: int = 10

    def run_once(self, now_ms: int) -> str | None:  # noqa: D401 - delegated
        """Persist the latest snapshot if available."""
        snap = self.source.get_latest()
        if snap is None:
            return None

        tick = int(snap["meta"]["tick"])
        name = f"{self.prefix}{tick:04d}"
        path = self.store.save(snap, name=name)

        save_dir = Path(self.store._dir)
        existing = sorted(save_dir.glob(f"{self.prefix}*.json"))
        if self.limit > 0 and len(existing) > self.limit:
            for old in existing[: -self.limit]:
                old.unlink(missing_ok=True)

        return path
