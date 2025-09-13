from __future__ import annotations

import random

from engine.m01_srs.solver import build_snapshot, make_initial_state, tick


def test_tick_deterministic() -> None:
    state = make_initial_state()
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    out1 = tick(state, 1.0, rng=rng1)
    out2 = tick(state, 1.0, rng=rng2)
    assert out1 == out2
    assert state == make_initial_state()  # original untouched


def test_battery_charge_discharge() -> None:
    state = make_initial_state()
    state["power"]["plant"]["online"] = False
    rng = random.Random(1)
    out = tick(state, 1.0, rng=rng)
    assert out["power"]["battery"]["kw"] < state["power"]["battery"]["kw"]

    state_on = make_initial_state()
    state_on["power"]["plant"]["online"] = True
    rng2 = random.Random(1)
    out_on = tick(state_on, 1.0, rng=rng2)
    assert out_on["power"]["battery"]["kw"] > state_on["power"]["battery"]["kw"]


def test_build_snapshot_shape() -> None:
    state = make_initial_state()
    snap = build_snapshot(state, 3, 1234)
    meta = snap["meta"]
    assert meta["tick"] == 3
    assert meta["ts_ms"] == 1234
    assert "schema" in meta and "version" in meta
    assert snap["state"] == state
