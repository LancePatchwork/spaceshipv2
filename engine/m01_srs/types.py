from __future__ import annotations

from typing import TypedDict


class PowerplantState(TypedDict):
    """State of the powerplant."""

    online: bool
    output_kw: float
    max_kw: float


class BatteryState(TypedDict):
    """Simple battery model."""

    kw: float
    capacity_kw: float
    max_charge_kw: float
    max_discharge_kw: float


class LifeSupportState(TypedDict):
    """Crew life support readings."""

    o2_pct: float
    temp_c: float
    crew_awake: int


class PowerState(TypedDict):
    plant: PowerplantState
    battery: BatteryState


class EnvState(TypedDict):
    ship_temp_c: float


class SRSState(TypedDict):
    power: PowerState
    life: LifeSupportState
    env: EnvState
