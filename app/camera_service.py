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

from view_transforms import apply_view_transforms, zoom_crop_pan

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

try:
    from dental_imaging.image_processing.color_adjustments import (
        ImageSettingsPercent,
        apply_software_image_adjustments,
    )

    _HAS_COLOR_ADJ = True
except Exception:  # pragma: no cover
    ImageSettingsPercent = None  # type: ignore[assignment,misc]
    apply_software_image_adjustments = None  # type: ignore[assignment,misc]
    _HAS_COLOR_ADJ = False

try:
    from dental_imaging.storage.snapshot_writer import SnapshotWriter

    _HAS_SNAPSHOT_WRITER = True
except Exception:  # pragma: no cover
    SnapshotWriter = None  # type: ignore[assignment,misc]
    _HAS_SNAPSHOT_WRITER = False

# Same mapping as dental_imaging ImageSettingsHardwareRange defaults.
EXPOSURE_US_MIN = 1000
EXPOSURE_US_MAX = 200_000
GAIN_MAX = 20.0

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
        self._capture_in_progress = False
        self._timer = QTimer(self)
        self._timer.setInterval(max(16, int(round(1000 / TARGET_FPS))))
        self._timer.timeout.connect(self._on_frame_tick)
        self._stats_t0 = time.perf_counter()
        self._snapshot_writer = (
            SnapshotWriter(PROJECT_ROOT / "captures", "png", jpeg_quality=94)
            if _HAS_SNAPSHOT_WRITER and SnapshotWriter is not None
            else None
        )
        self._bridge.exposureChanged.connect(self._on_bridge_exposure_changed)
        self._bridge.gainChanged.connect(self._on_bridge_gain_changed)
        self._bridge.imageSettingsDefaultsRestored.connect(
            self.on_image_settings_defaults_restored
        )
        self._bridge.captureClicked.connect(self.on_capture_requested)
        self._bridge.presetSaveRequested.connect(self.on_preset_save_requested)
        self._bridge.presetRecallRequested.connect(self.on_preset_recall_requested)

        self._presets_path = PROJECT_ROOT / "config" / "presets.json"
        self._presets: dict[str, dict] = {}
        self._load_presets()

    # ── Presets (3 slots) ───────────────────────────────────────────────────
    def _load_presets(self) -> None:
        self._presets = {}
        try:
            if not self._presets_path.is_file():
                return
            data = json.loads(self._presets_path.read_text(encoding="utf-8"))
            presets = data.get("presets", {})
            if isinstance(presets, dict):
                for k, v in presets.items():
                    if str(k) in ("0", "1", "2") and isinstance(v, dict):
                        self._presets[str(k)] = v
        except Exception:
            self._presets = {}

    def _save_presets(self) -> None:
        try:
            self._presets_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": 1, "presets": self._presets}
            self._presets_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:
            self._bridge.toast(f"Could not save presets: {exc}")

    def _preset_snapshot_from_bridge(self) -> dict:
        return {
            "brightness": int(self._bridge.brightness),
            "zoom": int(self._bridge.zoom),
            "previewPanX": float(self._bridge.previewPanX),
            "previewPanY": float(self._bridge.previewPanY),
            "flipHorizontal": bool(self._bridge.flipHorizontal),
            "flipVertical": bool(self._bridge.flipVertical),
            "rotateQuarterTurns": int(self._bridge.rotateQuarterTurns) % 4,
            "exposure": int(self._bridge.exposure),
            "gain": int(self._bridge.gain),
            "whiteBalance": int(self._bridge.whiteBalance),
            "contrast": int(self._bridge.contrast),
            "saturation": int(self._bridge.saturation),
            "warmth": int(self._bridge.warmth),
            "tint": int(self._bridge.tint),
            "captureFormatPng": bool(self._bridge.captureFormatPng),
            "imageQuality": int(self._bridge.imageQuality),
        }

    @pyqtSlot(int)
    def on_preset_save_requested(self, index: int) -> None:
        k = str(int(index))
        if k not in ("0", "1", "2"):
            return
        self._presets[k] = self._preset_snapshot_from_bridge()
        self._save_presets()
        self._bridge.toast(f"Preset {int(index) + 1} saved")

    @pyqtSlot(int)
    def on_preset_recall_requested(self, index: int) -> None:
        k = str(int(index))
        snap = self._presets.get(k)
        if not isinstance(snap, dict):
            self._bridge.toast(f"Preset {int(index) + 1} is empty — long-press to save")
            return

        try:
            self._bridge.apply_preset_snapshot(snap)
        except Exception:
            return

        # Ensure hardware follows recalled exposure/gain when connected.
        self._push_exposure_to_camera()
        self._push_gain_to_camera()

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

        # Apply any active preset after connecting so hardware settings are pushed.
        try:
            ap = int(self._bridge.activePreset)
            if ap in (0, 1, 2):
                self.on_preset_recall_requested(ap)
        except Exception:
            pass

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
        self._bridge.reset_live_view_navigation()
        self._bridge.push_frame(self._provider)
        self._bridge.toast("Camera disconnected")

    def _bridge_image_settings_snapshot(self) -> Any:
        return ImageSettingsPercent(
            exposure=int(self._bridge.exposure),
            gain=int(self._bridge.gain),
            white_balance=int(self._bridge.whiteBalance),
            contrast=int(self._bridge.contrast),
            saturation=int(self._bridge.saturation),
            warmth=int(self._bridge.warmth),
            tint=int(self._bridge.tint),
        )

    def _apply_software_image_adjustments(self, frame: np.ndarray) -> np.ndarray:
        if (
            not _HAS_COLOR_ADJ
            or apply_software_image_adjustments is None
            or ImageSettingsPercent is None
            or frame is None
            or frame.size == 0
        ):
            return frame
        try:
            return apply_software_image_adjustments(
                frame, self._bridge_image_settings_snapshot()
            )
        except Exception:
            return frame

    def _exposure_us_from_slider(self) -> int:
        pct = max(0, min(100, int(self._bridge.exposure)))
        span = EXPOSURE_US_MAX - EXPOSURE_US_MIN
        return int(EXPOSURE_US_MIN + span * pct / 100.0)

    def _gain_from_slider(self) -> float:
        pct = max(0, min(100, int(self._bridge.gain)))
        return GAIN_MAX * pct / 100.0

    def _on_bridge_exposure_changed(self, _v: int) -> None:
        if getattr(self._bridge, "_image_settings_resetting", False):
            return
        self._push_exposure_to_camera()

    def _on_bridge_gain_changed(self, _v: int) -> None:
        if getattr(self._bridge, "_image_settings_resetting", False):
            return
        self._push_gain_to_camera()

    def _push_exposure_to_camera(self) -> None:
        if self._camera is None or not self._bridge.connected:
            return
        if not getattr(self._camera, "is_connected", False):
            return
        try:
            self._camera.set_exposure(self._exposure_us_from_slider(), auto=False)
        except Exception:
            pass

    def _push_gain_to_camera(self) -> None:
        if self._camera is None or not self._bridge.connected:
            return
        if not getattr(self._camera, "is_connected", False):
            return
        try:
            self._camera.set_gain(self._gain_from_slider(), auto=False)
        except Exception:
            pass

    @pyqtSlot()
    def on_image_settings_defaults_restored(self) -> None:
        """Reset: neutral sliders + continuous AE / AGC / AWB on the Basler."""
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            return
        try:
            self._camera.set_exposure(0, auto=True)
            self._camera.set_gain(0.0, auto=True)
            self._camera.set_white_balance(auto=True)
        except Exception:
            pass

    def _on_frame_tick(self) -> None:
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            return
        try:
            frame: Optional[np.ndarray] = self._camera.grab_preview_frame()
        except Exception:
            frame = None
        if frame is None or frame.size == 0:
            return
        frame = self._apply_software_image_adjustments(frame)
        self._provider.update_overview(frame)
        cropped, x0, y0, cw, ch, fw, fh = zoom_crop_pan(
            frame,
            self._bridge.zoom,
            self._bridge.previewPanX,
            self._bridge.previewPanY,
        )
        self._bridge.update_minimap_from_crop(x0, y0, cw, ch, fw, fh)
        if cropped is None or cropped.size == 0:
            return
        out = apply_view_transforms(
            cropped,
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

    @pyqtSlot()
    def on_capture_requested(self) -> None:
        """Capture current view, apply active image settings, and save to disk."""
        if self._capture_in_progress:
            return
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            self._bridge.toast("Camera is not connected.")
            return
        if self._snapshot_writer is None:
            self._bridge.toast("Capture storage is unavailable in this build.")
            return

        self._capture_in_progress = True
        try:
            frame = self._camera.grab_still_frame()
            if frame is None or frame.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return

            frame = self._apply_software_image_adjustments(frame)
            cropped, *_ = zoom_crop_pan(
                frame,
                self._bridge.zoom,
                self._bridge.previewPanX,
                self._bridge.previewPanY,
            )
            if cropped is None or cropped.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return
            out = apply_view_transforms(
                cropped,
                flip_h=self._bridge.flipHorizontal,
                flip_v=self._bridge.flipVertical,
                rotate_q=self._bridge.rotateQuarterTurns,
            )
            if out is None or out.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return

            fmt = "png" if bool(self._bridge.captureFormatPng) else "jpg"
            self._snapshot_writer.set_image_format(fmt)
            self._snapshot_writer.set_jpeg_quality(int(self._bridge.imageQuality))
            result = self._snapshot_writer.save_bgr(out, prefix="capture")
            self._bridge.toast(f"Saved: {result.path.name}")
            try:
                self._bridge.captureSaved.emit(str(result.path), int(result.width), int(result.height))
            except Exception:
                pass
        except Exception as exc:
            self._bridge.toast(f"Capture failed: {exc}")
            try:
                self._bridge.captureFailed.emit(str(exc))
            except Exception:
                pass
        finally:
            self._capture_in_progress = False
