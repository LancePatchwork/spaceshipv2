from __future__ import annotations

import sys
from collections.abc import Callable
from typing import cast

from PySide6.QtWidgets import QApplication, QMainWindow


def create_app() -> QApplication:
    """Create or return the global :class:`QApplication` instance."""

    app = QApplication.instance()
    if app is None:
        # ``sys.argv`` is passed to enable command line integrations if needed.
        app = QApplication(sys.argv)
    return cast(QApplication, app)


def run_app(make_window: Callable[[], QMainWindow]) -> int:
    """Run a Qt application created via ``make_window``.

    ``make_window`` should return a fully configured ``QMainWindow``.
    """

    app = create_app()
    window = make_window()
    window.show()
    return int(app.exec())
