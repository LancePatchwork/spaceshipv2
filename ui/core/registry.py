"""Widget registry mapping ids to builder functions.

This registry allows containers to construct widgets by identifier, keeping
layout concerns separate from widget implementations (M12).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List

from ui.widgets.battery_panel import build as build_battery
from ui.widgets.life_panel import build as build_life
from ui.widgets.power_panel import build as build_power

from .contracts import Widget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
else:
    from PySide6.QtWidgets import QWidget

WidgetBuilder = Callable[[], Widget]

_REGISTRY: Dict[str, WidgetBuilder] = {}


def register(widget_id: str, builder: WidgetBuilder) -> None:
    """Register ``builder`` under ``widget_id``."""
    _REGISTRY[widget_id] = builder


def build(widget_id: str) -> QWidget | None:
    """Construct a widget by ``widget_id`` if registered."""
    factory = _REGISTRY.get(widget_id)
    if factory:
        from typing import cast

        return cast(QWidget, factory())
    return None


def ids() -> List[str]:
    """Return a sorted list of registered widget IDs."""
    return sorted(_REGISTRY)


# Register built-in widgets
register("power", build_power)
register("battery", build_battery)
register("life", build_life)
