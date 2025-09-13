from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import typer

from engine.lib.contracts import Snapshot, SnapshotSource
from ui.core.provider import PollingSnapshotProvider
from ui.windows.dashboard_tui import DashboardTUI


class InMemorySnapshotBus:
    """Simple in-memory bus implementing both source and sink."""

    def __init__(self) -> None:
        self._snap: Snapshot | None = None

    def publish(self, snap: Snapshot) -> None:
        self._snap = snap

    def get_latest(self) -> Snapshot | None:
        return self._snap


BUS = InMemorySnapshotBus()


class FileSnapshotSource:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._mtime = 0.0
        self._snap: Snapshot | None = None

    def get_latest(self) -> Snapshot | None:
        try:
            mtime = self._path.stat().st_mtime
        except FileNotFoundError:
            return self._snap
        if mtime > self._mtime:
            with self._path.open("r") as f:
                self._snap = cast(Snapshot, json.load(f))
            self._mtime = mtime
        return self._snap


def main(
    from_bus: bool = typer.Option(False, "--from-bus", help="Use in-memory bus"),
    from_file: Path | None = typer.Option(None, "--from-file", help="Read from snapshot file"),
) -> None:
    if from_bus == (from_file is not None):
        raise typer.BadParameter("Choose exactly one snapshot source")

    source: SnapshotSource
    if from_bus:
        source = BUS
    else:
        assert from_file is not None
        source = FileSnapshotSource(from_file)

    provider = PollingSnapshotProvider(source)
    DashboardTUI(provider).run()


if __name__ == "__main__":
    typer.run(main)
