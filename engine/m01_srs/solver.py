from __future__ import annotations

from copy import deepcopy
import random

from typing import cast

from .types import BatteryState, LifeSupportState, PowerplantState, SRSState
from engine.lib.contracts import SNAPSHOT_SCHEMA, SRS_VERSION, Snapshot


def make_initial_state() -> SRSState:
    return {
        "power": {
            "plant": {"online": False, "output_kw": 0.0, "max_kw": 100.0},
            "battery": {
                "kw": 50.0,
                "capacity_kw": 100.0,
                "max_charge_kw": 20.0,
                "max_discharge_kw": 20.0,
            },
        },
        "life": {"o2_pct": 21.0, "temp_c": 22.0, "crew_awake": 0},
        "env": {"ship_temp_c": 22.0},
    }


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def tick(state: SRSState, dt_s: float, *, rng: random.Random) -> SRSState:
    new_state: SRSState = deepcopy(state)

    plant: PowerplantState = new_state["power"]["plant"]
    battery: BatteryState = new_state["power"]["battery"]
    life: LifeSupportState = new_state["life"]
    env = new_state["env"]

    if plant["online"]:
        plant["output_kw"] = _clamp(plant["output_kw"] + 10.0 * dt_s, 0.0, plant["max_kw"])
    else:
        plant["output_kw"] = 0.0

    life_load_kw = 5.0 + 0.1 * float(life["crew_awake"])
    net_kw = plant["output_kw"] - life_load_kw

    if net_kw >= 0.0:
        charge_kw = min(net_kw, battery["max_charge_kw"])
        battery["kw"] = _clamp(battery["kw"] + charge_kw * dt_s, 0.0, battery["capacity_kw"])
    else:
        discharge_kw = min(-net_kw, battery["max_discharge_kw"])
        battery["kw"] = _clamp(battery["kw"] - discharge_kw * dt_s, 0.0, battery["capacity_kw"])

    life["o2_pct"] = _clamp(
        life["o2_pct"] + (21.0 - life["o2_pct"]) * 0.1 * dt_s + rng.random() * 0.05 - 0.025,
        0.0,
        100.0,
    )
    life["temp_c"] = _clamp(
        life["temp_c"] + (22.0 - life["temp_c"]) * 0.1 * dt_s + rng.random() * 0.05 - 0.025,
        -50.0,
        100.0,
    )

    env["ship_temp_c"] = _clamp(
        env["ship_temp_c"] + (life["temp_c"] - env["ship_temp_c"]) * 0.1 * dt_s,
        -50.0,
        100.0,
    )

    return new_state


def build_snapshot(state: SRSState, tick_idx: int, ts_ms: int) -> Snapshot:
    return {
        "meta": {
            "ts_ms": ts_ms,
            "tick": tick_idx,
            "schema": SNAPSHOT_SCHEMA,
            "version": SRS_VERSION,
        },
        "state": cast(dict[str, object], state),
    }
