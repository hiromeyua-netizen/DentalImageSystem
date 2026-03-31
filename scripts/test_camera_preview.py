"""Launch the kiosk UI (same as ``python app/main.py`` from repo root)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from main import main

if __name__ == "__main__":
    sys.exit(main())
