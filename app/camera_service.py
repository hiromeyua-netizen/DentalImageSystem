"""
Live camera session for the QML app: Basler detection, connect/disconnect, preview timer.

Expects project root on sys.path so ``dental_imaging`` imports resolve when running
``python app/main.py`` from the repository root.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from PyQt6.QtCore import QObject, QTimer, pyqtSlot

from view_transforms import apply_view_transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dental_imaging.hardware.camera import detect_cameras
    from dental_imaging.hardware.camera.basler_camera import BaslerCamera
    from dental_imaging.models.camera_config import CameraConfig

    _HAS_BASLER = True
except Exception:  # pragma: no cover - optional env without pypylon
    detect_cameras = None  # type: ignore[assignment,misc]
    BaslerCamera = None  # type: ignore[assignment,misc]
    CameraConfig = None  # type: ignore[assignment,misc]
    _HAS_BASLER = False

# Nominal stream rate (UI + timer; matches product reference / camera config).
TARGET_FPS = 31


class CameraService(QObject):
    """Drives ``FrameProvider`` + ``DentalBridge`` from a Basler camera when available."""

    def __init__(self, bridge: Any, provider: Any, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._bridge = bridge
        self._provider = provider
        self._camera: Any = None
        self._detected: List[Any] = []
        self._timer = QTimer(self)
        self._timer.setInterval(max(16, int(round(1000 / TARGET_FPS))))
        self._timer.timeout.connect(self._on_frame_tick)
        self._stats_t0 = time.perf_counter()

    # ── Detection ───────────────────────────────────────────────────────────
    def refresh_detection(self) -> None:
        if not _HAS_BASLER:
            self._detected = []
            self._bridge.set_camera_detection(0, "Industrial camera SDK unavailable")
            return
        try:
            cams = detect_cameras()
        except Exception as exc:  # pragma: no cover
            self._detected = []
            self._bridge.set_camera_detection(0, f"Detection failed: {exc}")
            return
        self._detected = list(cams)
        n = len(self._detected)
        if n == 0:
            self._bridge.set_camera_detection(0, "No camera detected")
            return
        first = self._detected[0]
        summary = f"{first.vendor_name} {first.model_name}"
        if n > 1:
            summary += f"  (+{n - 1} more)"
        self._bridge.set_camera_detection(n, summary)

    @pyqtSlot()
    def refresh_camera_detection(self) -> None:
        self.refresh_detection()

    @pyqtSlot()
    def auto_connect_if_available(self) -> None:
        """Connect on startup when at least one Basler camera is present."""
        if self._bridge.connected:
            return
        if not _HAS_BASLER or not self._detected:
            return
        self._connect()

    # ── Connect / disconnect (power button) ─────────────────────────────────
    @pyqtSlot()
    def toggle_connection(self) -> None:
        if self._bridge.connected:
            self._disconnect()
        else:
            self._connect()

    def _load_default_config(self) -> Any:
        path = PROJECT_ROOT / "config" / "camera_defaults.json"
        if not path.is_file():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return CameraConfig.from_dict(json.load(f))
        except Exception:
            return None

    def _connect(self) -> None:
        self.refresh_detection()
        if not _HAS_BASLER:
            self._bridge.toast("Industrial camera support is not available in this environment.")
            return
        if not self._detected:
            self._bridge.toast("No camera detected — check USB and drivers.")
            return
        if self._camera is not None and getattr(self._camera, "is_connected", False):
            return
        cam = None
        try:
            cam = BaslerCamera(self._detected[0])
            cam.connect()
            cfg = self._load_default_config()
            if cfg is not None:
                try:
                    cam.configure(cfg)
                except Exception as exc:
                    self._bridge.toast(f"Connected; using camera defaults ({exc})")
            cam.start_grabbing()
        except Exception as exc:
            self._bridge.toast(f"Could not connect: {exc}")
            if cam is not None:
                try:
                    cam.disconnect()
                except Exception:
                    pass
            self._camera = None
            return

        self._camera = cam
        self._bridge.set_connected(True)
        self._bridge.set_capturable(True)
        self._stats_t0 = time.perf_counter()
        self._timer.start()
        self._bridge.toast("Camera connected")

    def _disconnect(self) -> None:
        self._timer.stop()
        if self._camera is not None:
            try:
                self._camera.disconnect()
            except Exception:
                pass
            self._camera = None
        self._provider.reset_to_placeholder()
        self._bridge.set_connected(False)
        self._bridge.set_capturable(False)
        self._bridge.clear_stream_stats()
        self._bridge.push_frame(self._provider)
        self._bridge.toast("Camera disconnected")

    def _on_frame_tick(self) -> None:
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            return
        try:
            frame: Optional[np.ndarray] = self._camera.grab_preview_frame()
        except Exception:
            frame = None
        if frame is None or frame.size == 0:
            return
        out = apply_view_transforms(
            frame,
            flip_h=self._bridge.flipHorizontal,
            flip_v=self._bridge.flipVertical,
            rotate_q=self._bridge.rotateQuarterTurns,
        )
        if out is None or out.size == 0:
            return
        self._provider.update_frame(out)
        self._bridge.push_frame(self._provider)
        now = time.perf_counter()
        if now - self._stats_t0 < 0.45:
            return
        self._stats_t0 = now
        h, w = out.shape[:2]
        fps = float(TARGET_FPS)
        mbps = (w * h * 3.0 * fps) / (1024.0 * 1024.0)
        self._bridge.set_stats(w, h, fps, mbps)
