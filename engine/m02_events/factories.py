from __future__ import annotations

from typing import Literal

from engine.m02_events.models import Event


def make_red_alert_event(
    reason: Literal["combat", "collision", "boarders", "life_support"],
    auto_stations: bool,
) -> Event:
    return Event(
        type="alerts.red",
        category="alerts",
        priority=0,
        preemptible=False,
        audience_scope=["shipwide"],
        payload={"reason": reason, "auto_stations": auto_stations},
    )


def make_sleep_event(actor_id: str, duration_s: int) -> Event:
    if duration_s < 0:
        raise ValueError("duration_s must be non-negative")
    return Event(
        type="crew.sleep",
        category="crew_admin",
        priority=90,
        preemptible=True,
        audience_scope=[f"private:{actor_id}"],
        payload={"actor_id": actor_id, "duration_s": duration_s},
    )


def make_repair_event(
    system_id: str,
    location: str | None = None,
    severity: Literal["minor", "serious", "critical"] = "minor",
) -> Event:
    priorities: dict[str, int] = {"minor": 40, "serious": 20, "critical": 5}
    payload: dict[str, object] = {"system_id": system_id, "severity": severity}
    if location is not None:
        payload["location"] = location
    return Event(
        type="task.repair",
        category="engineering",
        priority=priorities[severity],
        preemptible=True,
        audience_scope=["department:engineering", "officers"],
        payload=payload,
    )


__all__ = [
    "make_red_alert_event",
    "make_sleep_event",
    "make_repair_event",
]
