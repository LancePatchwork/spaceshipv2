import heapq
import math
import os
from pathlib import Path
from typing import Literal, cast

import structlog
import typer

from engine.lib.rng import seed_for
from engine.m02_events.factories import make_red_alert_event, make_repair_event, make_sleep_event
from engine.m02_events.queue import EventQueue
from engine.m02_events.subscriptions import SubscriptionBroker

STATE_FILE = Path(os.environ.get("EVT_STATE_FILE", ".evt_state.pkl"))
SAVE_SEED = 123

if STATE_FILE.exists():
    with STATE_FILE.open("rb") as f:
        import pickle

        EQ, BROKER = pickle.load(f)
else:
    EQ = EventQueue()
    BROKER = SubscriptionBroker(EQ)


def _save_state() -> None:
    import pickle

    with STATE_FILE.open("wb") as f:
        pickle.dump((EQ, BROKER), f)


structlog.configure(processors=[structlog.processors.JSONRenderer()])
log = structlog.get_logger()

app = typer.Typer()


def _backfill(actor_id: str, scopes: list[str]) -> None:
    heap = BROKER._personal.setdefault(actor_id, [])
    existing_ids = {eid for *_, eid in heap}
    for event_id in EQ.list_by_scope("shipwide"):
        if event_id in existing_ids:
            continue
        e = EQ.get_by_id(event_id)
        if e is None:
            continue
        deadline_ts = e.deadline.timestamp() if e.deadline else math.inf
        tie_break = seed_for(SAVE_SEED, actor_id, e.id).random()
        heapq.heappush(heap, (e.priority, deadline_ts, tie_break, e.id))
        existing_ids.add(e.id)
    for scope in scopes:
        for event_id in EQ.list_by_scope(scope):
            if event_id in existing_ids:
                continue
            e = EQ.get_by_id(event_id)
            if e is None:
                continue
            deadline_ts = e.deadline.timestamp() if e.deadline else math.inf
            tie_break = seed_for(SAVE_SEED, actor_id, e.id).random()
            heapq.heappush(heap, (e.priority, deadline_ts, tie_break, e.id))
            existing_ids.add(e.id)


@app.command("spawn-red-alert")
def spawn_red_alert(
    reason: str = typer.Option(..., "--reason"),
    auto_stations: bool = typer.Option(True, "--auto-stations/--no-auto-stations"),
) -> None:
    e = make_red_alert_event(
        reason=cast(Literal["combat", "collision", "boarders", "life_support"], reason),
        auto_stations=auto_stations,
    )
    EQ.publish(e)
    BROKER.on_publish(e, SAVE_SEED)
    log.info("spawn_red_alert", evt=e.model_dump())
    _save_state()


@app.command("spawn-repair")
def spawn_repair(
    system_id: str = typer.Option(..., "--system-id"),
    severity: str = typer.Option("minor", "--severity"),
    location: str | None = typer.Option(None, "--location"),
) -> None:
    e = make_repair_event(
        system_id=system_id,
        severity=cast(Literal["minor", "serious", "critical"], severity),
        location=location,
    )
    EQ.publish(e)
    BROKER.on_publish(e, SAVE_SEED)
    log.info("spawn_repair", evt=e.model_dump())
    _save_state()


@app.command("spawn-sleep")
def spawn_sleep(
    actor_id: str = typer.Option(..., "--actor-id"),
    duration_s: int = typer.Option(..., "--duration-s"),
) -> None:
    e = make_sleep_event(actor_id=actor_id, duration_s=duration_s)
    EQ.publish(e)
    BROKER.on_publish(e, SAVE_SEED)
    log.info("spawn_sleep", evt=e.model_dump())
    _save_state()


@app.command()
def subscribe(
    actor_id: str = typer.Option(..., "--actor-id"),
    scopes: list[str] = typer.Option(..., "--scopes"),
) -> None:
    BROKER.subscribe(actor_id, *scopes)
    _backfill(actor_id, scopes)
    log.info("subscribe", actor_id=actor_id, scopes=scopes)
    _save_state()


@app.command("list")
def list_events(
    actor_id: str = typer.Option(..., "--actor-id"),
) -> None:
    heap = BROKER._personal.get(actor_id, [])
    events = []
    for prio, _, _, event_id in heapq.nsmallest(10, heap):
        e = EQ.get_by_id(event_id)
        if e is None:
            continue
        events.append({"id": e.id, "priority": prio})
    log.info("list", actor_id=actor_id, events=events)
    _save_state()


@app.command()
def claim(
    actor_id: str = typer.Option(..., "--actor-id"),
) -> None:
    e = BROKER.claim(actor_id)
    if e is None:
        log.info("claim", actor_id=actor_id, evt=None)
    else:
        log.info("claim", actor_id=actor_id, evt=e.model_dump())
    _save_state()


@app.command()
def done(
    actor_id: str = typer.Option(..., "--actor-id"),
    event_id: str = typer.Option(..., "--event-id"),
) -> None:
    BROKER.done(actor_id, event_id)
    e = EQ.get_by_id(event_id)
    if e is None:
        log.info("done", actor_id=actor_id, event_id=event_id, evt=None)
    else:
        log.info("done", actor_id=actor_id, evt=e.model_dump())
    _save_state()


if __name__ == "__main__":
    app()
