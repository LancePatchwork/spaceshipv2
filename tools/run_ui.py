from __future__ import annotations

from ui.core.app import run_app
from ui.windows.main_window import MainWindow


def main() -> int:
    return run_app(lambda: MainWindow())


if __name__ == "__main__":
    raise SystemExit(main())
