"""UI command definitions and event-queue bridge."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from engine.lib.contracts import EventQueueView


class UICommand(str, Enum):
    """Actions that the UI can request from the engine."""

    SAVE_SNAPSHOT = "ui.save_snapshot"
    LOAD_SNAPSHOT = "ui.load_snapshot"


def publish_ui_command(eq_view: EventQueueView, kind: str, payload: Dict[str, Any]) -> None:
    """Publish a UI command via the engine event queue.

    Per M02 all actions flow through the event system. This helper is a thin
    wrapper suitable for tests; production callers may supply an event queue
    view connected to the engine.
    """

    eq_view.publish_system_event(kind, payload)
