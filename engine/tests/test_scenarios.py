from __future__ import annotations

from typing import Iterable, cast

from engine.lib.contracts import Snapshot
from tools.scenario import simulate


def extract_battery(snaps: Iterable[Snapshot]) -> list[float]:
    res: list[float] = []
    for snap in snaps:
        state = snap["state"]
        power = cast(dict[str, object], state["power"])
        res.append(float(cast(float, power["battery_kw"])))
    return res


def test_plant_offline_discharges() -> None:
    snaps = simulate(steps=5, plant_online=False, crew_awake=5)
    batteries = extract_battery(snaps)
    assert all(b2 < b1 for b1, b2 in zip(batteries, batteries[1:]))


def test_plant_online_charges() -> None:
    snaps = simulate(steps=5, plant_online=True, crew_awake=5)
    batteries = extract_battery(snaps)
    assert all(b2 >= b1 for b1, b2 in zip(batteries, batteries[1:]))
