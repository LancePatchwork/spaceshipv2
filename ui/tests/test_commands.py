from __future__ import annotations

from typing import Any, Dict

from ui.core.commands import UICommand, publish_ui_command


class DummyQueue:
    def __init__(self) -> None:
        self.published: list[tuple[str, Dict[str, Any]]] = []

    def publish_system_event(self, kind: str, payload: Dict[str, Any]) -> None:
        self.published.append((kind, payload))


def test_publish_ui_command_calls_queue() -> None:
    q = DummyQueue()
    payload = {"name": "test"}
    publish_ui_command(q, UICommand.SAVE_SNAPSHOT.value, payload)
    assert q.published == [(UICommand.SAVE_SNAPSHOT.value, payload)]
