from __future__ import annotations

from PySide6.QtWidgets import QLabel  # type: ignore[import-untyped]

from ui.core.app import run_app
from ui.core.registry import WidgetRegistry
from ui.windows.main_window import MainWindow


def main() -> int:
    registry = WidgetRegistry()
    for name in ["Power", "Battery", "Life"]:
        registry.register(name, lambda n=name: QLabel(n))
    return run_app(lambda: MainWindow(registry))


if __name__ == "__main__":
    raise SystemExit(main())
