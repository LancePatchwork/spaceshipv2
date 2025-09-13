"""UI-facing data contracts and protocols.

These are pure typing constructs that define the shape of view-models and
interfaces used by the UI layer. Per M07, widgets only consume immutable
snapshots and never mutate engine state. M12 further requires widgets to be
self-contained, receiving data via ``set_view`` and exposing their name.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class RenderMeta(TypedDict):
    """Metadata describing a rendered snapshot."""

    tick: int
    ts_ms: int


class PowerVM(TypedDict):
    """Power plant output view-model."""

    plant_kw: float
    plant_max_kw: float


class BatteryVM(TypedDict):
    """Battery status view-model."""

    kw: float
    capacity_kw: float


class LifeVM(TypedDict):
    """Life-support view-model."""

    o2_pct: float
    life_temp_c: float
    ship_temp_c: float
    crew_awake: int


class DashboardVM(TypedDict):
    """Aggregate dashboard view-model presented to the UI."""

    meta: RenderMeta
    power: PowerVM
    battery: BatteryVM
    life: LifeVM


class Widget(Protocol):
    """Protocol implemented by dashboard widgets.

    Widgets are provided immutable view-models via ``set_view``. They expose a
    human-readable ``name`` used by container windows (M12)."""

    def set_view(self, vm: dict[str, object]) -> None: ...

    def name(self) -> str: ...


class SnapshotProvider(Protocol):
    """Retrieve the latest published snapshot.

    Implementations cache snapshots and ensure consumers only observe atomic
    updates per M07."""

    def get_latest(self) -> dict[str, object] | None: ...
