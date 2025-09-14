from __future__ import annotations

from typing import Iterable

from ui.core.poller import SnapshotPoller


class FakeProvider:
    def __init__(self, snaps: Iterable[dict[str, object] | None]) -> None:
        self._snaps = iter(snaps)

    def get_latest(self) -> dict[str, object] | None:
        return next(self._snaps, None)


class DummyWidget:
    def __init__(self) -> None:
        self.views: list[dict[str, object]] = []

    def set_view(self, vm: dict[str, object]) -> None:
        self.views.append(vm)

    def name(self) -> str:  # pragma: no cover - not used
        return "dummy"


def _make_snap(tick: int, plant: float) -> dict[str, object]:
    return {
        "meta": {"tick": tick, "ts_ms": tick * 100},
        "state": {
            "power": {"plant_kw": plant, "plant_max_kw": plant * 2},
            "battery": {"kw": plant * 3, "capacity_kw": plant * 4},
            "life": {
                "o2_pct": plant * 5,
                "life_temp_c": plant * 6,
                "ship_temp_c": plant * 7,
                "crew_awake": int(plant),
            },
        },
    }


def test_snapshot_poller_updates_widgets() -> None:
    provider = FakeProvider([_make_snap(1, 1.0), _make_snap(2, 2.0)])
    pw = DummyWidget()
    bw = DummyWidget()
    poller = SnapshotPoller(provider, {"power": pw, "battery": bw})

    poller._on_tick()
    assert pw.views[-1] == {"plant_kw": 1.0, "plant_max_kw": 2.0}
    assert bw.views[-1] == {"kw": 3.0, "capacity_kw": 4.0}

    poller._on_tick()
    assert pw.views[-1] == {"plant_kw": 2.0, "plant_max_kw": 4.0}
    assert bw.views[-1] == {"kw": 6.0, "capacity_kw": 8.0}


def test_snapshot_poller_handles_none() -> None:
    provider = FakeProvider([None, _make_snap(1, 1.0)])
    widget = DummyWidget()
    poller = SnapshotPoller(provider, {"power": widget})

    poller._on_tick()  # Should not crash when None
    assert widget.views == []

    poller._on_tick()
    assert widget.views[-1] == {"plant_kw": 1.0, "plant_max_kw": 2.0}
