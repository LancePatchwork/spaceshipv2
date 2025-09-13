from __future__ import annotations

from typing import Dict, List

from engine.m02_events.models import Event


class EventQueue:
    def __init__(self, capacity: int = 10_000) -> None:
        self.capacity = capacity
        self._events: Dict[str, Event] = {}
        self._by_category: Dict[str, List[str]] = {}
        self._by_scope: Dict[str, List[str]] = {}

    def publish(self, e: Event) -> None:
        if len(self._events) >= self.capacity:
            raise RuntimeError("queue capacity exceeded")
        self._events[e.id] = e
        if e.category:
            self._by_category.setdefault(e.category, []).append(e.id)
        for scope in e.audience_scope:
            self._by_scope.setdefault(scope, []).append(e.id)

    def update(self, e: Event) -> None:
        old = self._events.get(e.id)
        if old is None:
            raise KeyError(f"event {e.id} not found")
        if old.category:
            cat_list = self._by_category.get(old.category, [])
            if e.id in cat_list:
                cat_list.remove(e.id)
        for scope in old.audience_scope:
            scope_list = self._by_scope.get(scope, [])
            if e.id in scope_list:
                scope_list.remove(e.id)
        self._events[e.id] = e
        if e.category:
            self._by_category.setdefault(e.category, []).append(e.id)
        for scope in e.audience_scope:
            self._by_scope.setdefault(scope, []).append(e.id)
        e.append_audit("system", "update")

    def get_by_id(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_by_category(self, category: str) -> list[str]:
        return list(self._by_category.get(category, []))

    def list_by_scope(self, scope: str) -> list[str]:
        return list(self._by_scope.get(scope, []))


__all__ = ["EventQueue"]
