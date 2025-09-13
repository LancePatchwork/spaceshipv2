from __future__ import annotations

import random
from typing import Protocol, TypedDict

SNAPSHOT_SCHEMA = "starship.snap/v1"
SRS_VERSION = "0.1.0"


class SnapshotMeta(TypedDict):
    ts_ms: int
    tick: int
    schema: str
    version: str


class Snapshot(TypedDict):
    meta: SnapshotMeta
    state: dict[str, object]


class SnapshotSource(Protocol):
    def get_latest(self) -> Snapshot | None: ...


class SnapshotSink(Protocol):
    def publish(self, snap: Snapshot) -> None: ...


class SaveStore(Protocol):
    def save(self, snap: Snapshot, *, name: str) -> str: ...

    def load(self, name: str) -> Snapshot: ...


class TickSolver(Protocol):
    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]: ...


class EventQueueView(Protocol):
    def publish_system_event(self, kind: str, payload: dict[str, object]) -> None: ...
