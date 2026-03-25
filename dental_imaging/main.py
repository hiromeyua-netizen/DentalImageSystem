"""
Main entry point for the Dental Imaging System (Phase 1: camera preview and capture).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Must be set before any Qt/QML module is imported so the QML engine picks up
# the Basic (non-native) style, which allows Slider background/handle overrides.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PyQt6.QtWidgets import QApplication

# Package root (directory containing ``dental_imaging``) when running from source.
_PACKAGE_PARENT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_PARENT))

from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.settings import (
    load_app_settings,
    resolve_camera_defaults_path,
    resolve_default_config_path,
)
from dental_imaging.ui.main_window import MainWindow


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dental Imaging System")
    parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        help="Path to default_config.json (default: auto-detect)",
    )
    parser.add_argument(
        "--camera-config",
        type=Path,
        default=None,
        help="Path to camera_defaults.json (default: auto-detect)",
    )
    parser.add_argument(
        "--no-fullscreen",
        action="store_true",
        help="Run in a normal window instead of fullscreen",
    )
    parser.add_argument(
        "--no-auto-preview",
        action="store_true",
        help="Do not start live preview after the camera connects",
    )
    return parser.parse_args(argv)


def _load_camera_config(path: Path) -> CameraConfig:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return CameraConfig.from_dict(data)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    app_config_path = args.app_config or resolve_default_config_path()
    camera_config_path = args.camera_config or resolve_camera_defaults_path()

    try:
        app_settings = load_app_settings(app_config_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: Invalid application config: {e}", file=sys.stderr)
        return 1

    try:
        camera_config = _load_camera_config(camera_config_path)
    except FileNotFoundError:
        print(f"ERROR: Camera config not found: {camera_config_path}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"ERROR: Invalid camera config: {e}", file=sys.stderr)
        return 1

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(app_settings.application.name)
    qt_app.setApplicationVersion(app_settings.application.version)

    window = MainWindow(app_settings=app_settings)

    if not window.initialize_camera(camera_config):
        return 1

    auto_preview = app_settings.application.auto_start_preview and not args.no_auto_preview
    if auto_preview:
        window.start_preview()

    window.show()

    use_fullscreen = app_settings.application.fullscreen and not args.no_fullscreen
    if use_fullscreen:
        window.showFullScreen()

    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
