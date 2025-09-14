from __future__ import annotations

from collections.abc import Callable
from typing import Dict

from PySide6.QtWidgets import QWidget


class WidgetRegistry:
    """Registry mapping names to widget factories.

    Widgets register themselves with a factory callable returning a ``QWidget``.
    ``create`` instantiates a widget by name, raising ``KeyError`` if unknown.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[], QWidget]] = {}

    def register(self, name: str, factory: Callable[[], QWidget]) -> None:
        """Register a factory under ``name``.

        If ``name`` already exists it is overwritten.
        """

        self._factories[name] = factory

    def create(self, name: str) -> QWidget:
        """Create a widget by ``name``.

        Raises ``KeyError`` if the name is not registered.
        """

        factory = self._factories[name]
        return factory()
