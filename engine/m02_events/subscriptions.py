from __future__ import annotations

import heapq
import math
from typing import Dict, List, Set, Tuple

from engine.lib.rng import seed_for
from engine.m02_events.models import Event
from engine.m02_events.queue import EventQueue
from engine.m02_events.scheduling import should_preempt


class SubscriptionBroker:
    def __init__(self, eq: EventQueue) -> None:
        self._eq = eq
        self._personal: Dict[str, List[Tuple[float, float, float, str]]] = {}
        self._subscriptions: Dict[str, Set[str]] = {}

    def subscribe(self, actor_id: str, *scopes: str) -> None:
        subs = self._subscriptions.setdefault(actor_id, set())
        subs.update(scopes)
        self._personal.setdefault(actor_id, [])

    def unsubscribe(self, actor_id: str, *scopes: str) -> None:
        subs = self._subscriptions.get(actor_id)
        if not subs:
            return
        for scope in scopes:
            subs.discard(scope)

    def on_publish(self, e: Event, save_seed: int) -> None:
        for actor_id, scopes in self._subscriptions.items():
            if "shipwide" not in e.audience_scope and not (set(e.audience_scope) & scopes):
                continue
            # Preemption check: if actor has an active event that should be
            # preempted by the incoming event, suspend and requeue it.
            active = None
            for ev in self._eq._events.values():
                if ev.taker == actor_id and ev.state == "active":
                    active = ev
                    break
            if active and should_preempt(active, e):
                active.state = "suspended"
                active.append_audit(actor_id, "suspend")
                self._eq.update(active)
                heap = self._personal.setdefault(actor_id, [])
                deadline_ts = active.deadline.timestamp() if active.deadline else math.inf
                tie_break = seed_for(save_seed, actor_id, active.id).random()
                heapq.heappush(heap, (active.priority, deadline_ts, tie_break, active.id))

            heap = self._personal.setdefault(actor_id, [])
            deadline_ts = e.deadline.timestamp() if e.deadline else math.inf
            tie_break = seed_for(save_seed, actor_id, e.id).random()
            heapq.heappush(heap, (e.priority, deadline_ts, tie_break, e.id))


    def _next_event_id(self, actor_id: str) -> str | None:
        heap = self._personal.get(actor_id)
        if not heap:
            return None
        while heap:
            _, _, _, event_id = heap[0]
            e = self._eq.get_by_id(event_id)
            if e is None:
                heapq.heappop(heap)
                continue
            if e.state == "queued":
                return event_id
            if e.state == "suspended" and e.taker == actor_id:
                return event_id
            # otherwise remove stale reference
            heapq.heappop(heap)
        return None

    def peek(self, actor_id: str) -> Event | None:
        event_id = self._next_event_id(actor_id)
        if event_id is None:
            return None
        return self._eq.get_by_id(event_id)

    def claim(self, actor_id: str) -> Event | None:
        heap = self._personal.get(actor_id)
        if not heap:
            return None
        while heap:
            _, _, _, event_id = heapq.heappop(heap)
            e = self._eq.get_by_id(event_id)
            if e is None or e.state != "queued":
                continue
            e.state = "claimed"
            e.taker = actor_id
            e.append_audit(actor_id, "claim")
            self._eq.update(e)
            return e
        return None

    def mark_active(self, actor_id: str, event_id: str) -> None:
        e = self._eq.get_by_id(event_id)
        if e is None or e.taker != actor_id:
            raise KeyError(event_id)
        if e.state not in {"claimed", "suspended"}:
            raise ValueError("invalid state")
        e.state = "active"
        e.append_audit(actor_id, "active")
        self._eq.update(e)

    def done(self, actor_id: str, event_id: str) -> None:
        e = self._eq.get_by_id(event_id)
        if e is None or e.taker != actor_id:
            raise KeyError(event_id)
        e.state = "done"
        e.append_audit(actor_id, "done")
        self._eq.update(e)

    def suspend(self, actor_id: str, event_id: str) -> None:
        e = self._eq.get_by_id(event_id)
        if e is None or e.taker != actor_id:
            raise KeyError(event_id)
        if e.state != "active":
            raise ValueError("invalid state")
        e.state = "suspended"
        e.append_audit(actor_id, "suspend")
        self._eq.update(e)


__all__ = ["SubscriptionBroker"]
