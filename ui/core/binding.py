"""Helpers converting engine snapshots into UI view-models."""

from __future__ import annotations

from typing import Mapping, TypeAlias, cast

from .contracts import BatteryVM, DashboardVM, LifeVM, PowerVM, RenderMeta

Numeric: TypeAlias = int | float | str | bytes | bytearray


def _get_float(d: Mapping[str, object], key: str) -> float:
    value = d.get(key, 0.0)
    try:
        return float(cast(Numeric, value))
    except (TypeError, ValueError):
        return 0.0


def _get_int(d: Mapping[str, object], key: str) -> int:
    value = d.get(key, 0)
    try:
        return int(cast(Numeric, value))
    except (TypeError, ValueError):
        return 0


def to_dashboard_vm(snap: Mapping[str, object]) -> DashboardVM:
    """Build a :class:`DashboardVM` from a raw snapshot.

    Missing fields are filled with zeros to keep the UI stable and predictable.
    The function never raises; callers should guard against ``snap is None``
    prior to calling.
    """

    meta_src = cast(Mapping[str, object], snap.get("meta", {}))
    state = cast(Mapping[str, object], snap.get("state", {}))

    power_src = cast(Mapping[str, object], state.get("power", {}))
    battery_src = cast(Mapping[str, object], state.get("battery", {}))
    life_src = cast(Mapping[str, object], state.get("life", {}))

    meta: RenderMeta = {
        "tick": _get_int(meta_src, "tick"),
        "ts_ms": _get_int(meta_src, "ts_ms"),
    }
    power: PowerVM = {
        "plant_kw": _get_float(power_src, "plant_kw"),
        "plant_max_kw": _get_float(power_src, "plant_max_kw"),
    }
    battery: BatteryVM = {
        "kw": _get_float(battery_src, "kw"),
        "capacity_kw": _get_float(battery_src, "capacity_kw"),
    }
    life: LifeVM = {
        "o2_pct": _get_float(life_src, "o2_pct"),
        "life_temp_c": _get_float(life_src, "life_temp_c"),
        "ship_temp_c": _get_float(life_src, "ship_temp_c"),
        "crew_awake": _get_int(life_src, "crew_awake"),
    }

    return {
        "meta": meta,
        "power": power,
        "battery": battery,
        "life": life,
    }
