from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import typer  # type: ignore[import-not-found]

from engine.lib.contracts import (
    SNAPSHOT_SCHEMA,
    SRS_VERSION,
    SaveStore,
    Snapshot,
    SnapshotMeta,
    TickSolver,
)


@dataclass
class SimpleSolver(TickSolver):
    plant_gen_kw: float = 10.0
    crew_use_kw: float = 1.0

    def tick(
        self, state: dict[str, object], dt_s: float, *, rng: random.Random
    ) -> dict[str, object]:
        power = cast(dict[str, object], state.get("power", {}))
        life = cast(dict[str, object], state.get("life", {}))
        battery_kw = float(cast(float, power.get("battery_kw", 100.0)))
        plant_online = bool(cast(bool, power.get("plant_online", True)))
        crew_awake = int(cast(int, life.get("crew_awake", 0)))

        if plant_online:
            battery_kw += self.plant_gen_kw * dt_s
        battery_kw -= crew_awake * self.crew_use_kw * dt_s

        return {
            "power": {"battery_kw": battery_kw, "plant_online": plant_online},
            "life": {"crew_awake": crew_awake},
        }


def build_snapshot(state: dict[str, object], tick: int) -> Snapshot:
    meta: SnapshotMeta = {
        "ts_ms": int(time.time() * 1000),
        "tick": tick,
        "schema": SNAPSHOT_SCHEMA,
        "version": SRS_VERSION,
    }
    return {"meta": meta, "state": state}


class InMemoryPublisher:
    def __init__(self) -> None:
        self._snap: Snapshot | None = None

    def publish(self, snap: Snapshot) -> None:
        self._snap = snap

    def get_latest(self) -> Snapshot | None:
        return self._snap


class JsonSaveStore(SaveStore):
    def save(self, snap: Snapshot, *, name: str) -> str:  # pragma: no cover - simple IO
        path = Path(name)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w") as f:
            json.dump(snap, f)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
        return str(path)

    def load(self, name: str) -> Snapshot:  # pragma: no cover - unused
        path = Path(name)
        with path.open() as f:
            return cast(Snapshot, json.load(f))


def simulate(
    steps: int,
    *,
    plant_online: bool,
    crew_awake: int,
    rng: random.Random | None = None,
) -> list[Snapshot]:
    rng = rng or random.Random()
    solver = SimpleSolver()
    publisher = InMemoryPublisher()

    state: dict[str, object] = solver.tick({}, 0.0, rng=rng)
    snapshots: list[Snapshot] = [build_snapshot(state, 0)]

    for tick in range(1, steps + 1):
        power = cast(dict[str, object], state.get("power", {}))
        life = cast(dict[str, object], state.get("life", {}))
        state = {
            **state,
            "power": {**power, "plant_online": plant_online},
            "life": {**life, "crew_awake": crew_awake},
        }
        state = solver.tick(state, 1.0, rng=rng)
        snap = build_snapshot(state, tick)
        publisher.publish(snap)
        snapshots.append(snap)

    return snapshots


app = typer.Typer()


@app.callback()  # type: ignore[misc]
def main() -> None:
    """Scenario generator."""
    pass


@app.command()  # type: ignore[misc]
def run(
    steps: int = typer.Option(30, "--steps"),
    plant_online: bool = typer.Option(False, "--plant-online/--plant-offline"),
    crew_awake: int = typer.Option(0, "--crew-awake"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    snaps = simulate(steps, plant_online=plant_online, crew_awake=crew_awake)
    final = snaps[-1]
    store = JsonSaveStore()
    store.save(final, name=str(out))


if __name__ == "__main__":
    app()
