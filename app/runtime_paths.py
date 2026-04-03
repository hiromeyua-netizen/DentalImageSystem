"""
Resolve folders for development vs PyInstaller-frozen executable.

When frozen, ``config/`` and ``captures/`` live next to the ``.exe`` (writable).
QML and resources are unpacked under ``sys._MEIPASS`` at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """
    Root folder containing ``config/``, ``captures/``, etc.

    - Frozen: directory of the ``.exe`` (ship ``config`` beside the executable).
    - Dev: repository root (parent of ``app/``).
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def qml_root() -> Path:
    """Directory that contains ``main.qml``."""
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "app" / "qml"
    return Path(__file__).resolve().parent / "qml"
