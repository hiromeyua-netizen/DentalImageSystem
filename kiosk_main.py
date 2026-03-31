"""
Console entry point for packaged installs: adds ``app/`` to ``sys.path`` then runs the kiosk UI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    app_dir = Path(__file__).resolve().parent / "app"
    app_dir_str = str(app_dir)
    if app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)
    from main import main as run_app  # noqa: E402 — after path setup

    return int(run_app())


if __name__ == "__main__":
    raise SystemExit(main())
