"""
Load application-wide settings from ``config/default_config.json``.

Phase 1 uses preview dimensions, FPS, storage defaults, and window behavior.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ApplicationMeta:
    name: str
    version: str
    kiosk_mode: bool
    fullscreen: bool
    splash_screen_duration_ms: int
    auto_start_preview: bool


@dataclass(frozen=True)
class PreviewSettings:
    width: int
    height: int
    fps: float


@dataclass(frozen=True)
class StorageSettings:
    default_path: str
    default_format: str
    auto_organize: bool


@dataclass(frozen=True)
class ApplicationSettings:
    application: ApplicationMeta
    preview: PreviewSettings
    storage: StorageSettings


def load_app_settings(path: Path) -> ApplicationSettings:
    """
    Parse ``default_config.json`` into structured settings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required keys are missing or invalid.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Application config not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = json.load(f)

    app = raw.get("application") or {}
    preview = raw.get("preview") or {}
    storage = raw.get("storage") or {}
    preview_res = preview.get("resolution") or {}

    try:
        meta = ApplicationMeta(
            name=str(app.get("name", "Dental Imaging System")),
            version=str(app.get("version", "0.1.0")),
            kiosk_mode=bool(app.get("kiosk_mode", True)),
            fullscreen=bool(app.get("fullscreen", True)),
            splash_screen_duration_ms=int(app.get("splash_screen_duration", 2000)),
            auto_start_preview=bool(app.get("auto_start_preview", True)),
        )
        prev = PreviewSettings(
            width=int(preview_res.get("width", 1920)),
            height=int(preview_res.get("height", 1080)),
            fps=float(preview.get("fps", 30)),
        )
        stor = StorageSettings(
            default_path=str(storage.get("default_path", "DentalImages")),
            default_format=str(storage.get("default_format", "png")).lower(),
            auto_organize=bool(storage.get("auto_organize", True)),
        )
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid application config: {path}") from e

    if prev.width <= 0 or prev.height <= 0:
        raise ValueError("Preview resolution width and height must be positive")
    if prev.fps <= 0:
        raise ValueError("Preview fps must be positive")
    if stor.default_format not in ("png", "jpg", "jpeg", "tif", "tiff", "bmp"):
        raise ValueError(
            f"Unsupported storage.default_format: {stor.default_format!r}"
        )

    return ApplicationSettings(application=meta, preview=prev, storage=stor)


def resolve_default_config_path() -> Path:
    """
    Locate ``default_config.json`` for the running environment.

    Resolution order:
    1. ``DENTAL_IMAGING_ROOT/config/default_config.json`` if the env var is set
       and the file exists
    2. ``<cwd>/config/default_config.json`` if it exists
    3. Repository layout relative to this package: ``<repo>/config/default_config.json``
    """
    env = os.environ.get("DENTAL_IMAGING_ROOT")
    if env:
        candidate = Path(env).expanduser().resolve() / "config" / "default_config.json"
        if candidate.is_file():
            return candidate

    cwd_candidate = (Path.cwd() / "config" / "default_config.json").resolve()
    if cwd_candidate.is_file():
        return cwd_candidate

    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "config" / "default_config.json"


def resolve_camera_defaults_path() -> Path:
    """Locate ``camera_defaults.json`` using the same rules as :func:`resolve_default_config_path`."""
    env = os.environ.get("DENTAL_IMAGING_ROOT")
    if env:
        candidate = Path(env).expanduser().resolve() / "config" / "camera_defaults.json"
        if candidate.is_file():
            return candidate

    cwd_candidate = (Path.cwd() / "config" / "camera_defaults.json").resolve()
    if cwd_candidate.is_file():
        return cwd_candidate

    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "config" / "camera_defaults.json"


def resolve_storage_directory(settings: ApplicationSettings, base: Optional[Path] = None) -> Path:
    """
    Resolve the directory used for Phase 1 captures.

    Relative ``storage.default_path`` is resolved under ``base`` (typically the
    user's home directory). Absolute paths are used as-is.
    """
    p = Path(settings.storage.default_path)
    if p.is_absolute():
        return p
    root = base if base is not None else Path.home()
    return (root / p).resolve()
