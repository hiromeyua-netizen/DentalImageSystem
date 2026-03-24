"""Tests for application settings loading."""

import json
from pathlib import Path

import pytest

from dental_imaging.settings.app_settings import (
    load_app_settings,
    resolve_storage_directory,
)


def test_load_app_settings_minimal(tmp_path: Path) -> None:
    path = tmp_path / "default_config.json"
    path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "Test App",
                    "version": "1.0.0",
                    "kiosk_mode": False,
                    "fullscreen": False,
                    "splash_screen_duration": 1000,
                    "auto_start_preview": False,
                },
                "preview": {"resolution": {"width": 640, "height": 480}, "fps": 15},
                "storage": {
                    "default_path": "Out",
                    "default_format": "png",
                    "auto_organize": True,
                },
            }
        ),
        encoding="utf-8",
    )
    s = load_app_settings(path)
    assert s.application.name == "Test App"
    assert s.preview.width == 640 and s.preview.height == 480
    assert s.preview.fps == 15.0
    assert s.storage.default_format == "png"


def test_resolve_storage_directory_relative(tmp_path: Path) -> None:
    path = tmp_path / "default_config.json"
    path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "X",
                    "version": "0",
                    "kiosk_mode": True,
                    "fullscreen": True,
                    "splash_screen_duration": 0,
                    "auto_start_preview": True,
                },
                "preview": {"resolution": {"width": 1, "height": 1}, "fps": 1},
                "storage": {
                    "default_path": "DentalImages",
                    "default_format": "png",
                    "auto_organize": True,
                },
            }
        ),
        encoding="utf-8",
    )
    s = load_app_settings(path)
    out = resolve_storage_directory(s, base=tmp_path)
    assert out == (tmp_path / "DentalImages").resolve()


def test_load_app_settings_bad_format(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "X",
                    "version": "0",
                    "kiosk_mode": True,
                    "fullscreen": True,
                    "splash_screen_duration": 0,
                    "auto_start_preview": True,
                },
                "preview": {"resolution": {"width": 1, "height": 1}, "fps": 1},
                "storage": {
                    "default_path": "x",
                    "default_format": "gif",
                    "auto_organize": True,
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unsupported"):
        load_app_settings(path)
