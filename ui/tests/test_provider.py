from __future__ import annotations

from engine.lib.contracts import Snapshot
from ui.core.provider import PollingSnapshotProvider


class DummySource:
    def __init__(self, snap: Snapshot | None) -> None:
        self._snap = snap
        self.calls = 0

    def get_latest(self) -> Snapshot | None:
        self.calls += 1
        return self._snap


def test_provider_returns_snapshot() -> None:
    snap: Snapshot = {
        "meta": {"ts_ms": 1, "tick": 0, "schema": "starship.snap/v1", "version": "0.1.0"},
        "state": {"power": {}, "life": {}, "env": {}},
    }
    src = DummySource(snap)
    provider = PollingSnapshotProvider(src, interval_ms=1000)
    assert provider.get_latest() is snap
    assert provider.get_latest() is snap
    assert src.calls == 1
