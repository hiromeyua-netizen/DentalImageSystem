"""
Live camera session for the QML app: Basler detection, connect/disconnect, preview timer.

Run from repo root: ``python app/main.py`` (adds the ``app`` directory to ``sys.path``).
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from PyQt6.QtCore import QObject, QTimer, pyqtSlot

from view_transforms import apply_view_transforms, zoom_crop_pan
from runtime_paths import project_root

PROJECT_ROOT = project_root()

try:
    from camera_core.hardware.camera import detect_cameras
    from camera_core.hardware.camera.basler_camera import BaslerCamera
    from camera_core.models.camera_config import CameraConfig

    _HAS_BASLER = True
except Exception:  # pragma: no cover - optional env without pypylon
    detect_cameras = None  # type: ignore[assignment,misc]
    BaslerCamera = None  # type: ignore[assignment,misc]
    CameraConfig = None  # type: ignore[assignment,misc]
    _HAS_BASLER = False

try:
    from camera_core.image_processing.color_adjustments import (
        ImageSettingsPercent,
        apply_auto_color_balance,
        apply_software_image_adjustments,
        compute_auto_color_gains,
    )

    _HAS_COLOR_ADJ = True
except Exception:  # pragma: no cover
    ImageSettingsPercent = None  # type: ignore[assignment,misc]
    apply_software_image_adjustments = None  # type: ignore[assignment,misc]
    apply_auto_color_balance = None  # type: ignore[assignment,misc]
    compute_auto_color_gains = None  # type: ignore[assignment,misc]
    _HAS_COLOR_ADJ = False

try:
    from camera_core.storage.snapshot_writer import SnapshotWriter

    _HAS_SNAPSHOT_WRITER = True
except Exception:  # pragma: no cover
    SnapshotWriter = None  # type: ignore[assignment,misc]
    _HAS_SNAPSHOT_WRITER = False

# Slider → hardware μs / dB mapping (paired with ``ImageSettingsPercent`` neutral 50).
EXPOSURE_US_MIN = 1000
EXPOSURE_US_MAX = 200_000
GAIN_MAX = 20.0

# Nominal stream rate (UI + timer; matches product reference / camera config).
TARGET_FPS = 31
BURST_DEFAULT_COUNT = 10
STORAGE_CONFIG_PATH = PROJECT_ROOT / "config" / "storage_config.json"
DEFAULT_STORAGE_WARN_FREE_BYTES = 1 * 1024 * 1024 * 1024      # 1 GiB
DEFAULT_STORAGE_MIN_CAPTURE_FREE_BYTES = 256 * 1024 * 1024    # 256 MiB
DEFAULT_ESTIMATED_CAPTURE_BYTES = 25 * 1024 * 1024            # conservative single capture estimate


class CameraService(QObject):
    """Drives ``FrameProvider`` + ``DentalBridge`` from a Basler camera when available."""

    def __init__(self, bridge: Any, provider: Any, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._bridge = bridge
        self._provider = provider
        self._camera: Any = None
        self._detected: List[Any] = []
        self._capture_in_progress = False
        self._burst_timer = QTimer(self)
        self._burst_timer.setSingleShot(True)
        self._burst_timer.timeout.connect(self._on_burst_tick)
        self._capture_delay_timer = QTimer(self)
        self._capture_delay_timer.setSingleShot(True)
        self._capture_delay_timer.timeout.connect(self._on_capture_delay_elapsed)
        self._pending_capture_mode = ""  # "", "snapshot", "burst"
        self._burst_active = False
        self._burst_stop_requested = False
        self._burst_index = 0
        self._burst_total = max(1, int(getattr(self._bridge, "captureBurstCount", BURST_DEFAULT_COUNT)))
        self._timer = QTimer(self)
        self._timer.setInterval(max(16, int(round(1000 / TARGET_FPS))))
        self._timer.timeout.connect(self._on_frame_tick)
        self._stats_t0 = time.perf_counter()
        self._last_storage_warn_t = 0.0
        self._storage_space_cfg: dict[str, int] = {}
        self._system_capture_dir = PROJECT_ROOT / "captures"
        self._storage_switch_internal = False
        self._snapshot_writer = None
        self._bridge.exposureChanged.connect(self._on_bridge_exposure_changed)
        self._bridge.gainChanged.connect(self._on_bridge_gain_changed)
        self._bridge.imageSettingsDefaultsRestored.connect(
            self.on_image_settings_defaults_restored
        )
        self._bridge.captureClicked.connect(self.on_capture_requested)
        self._bridge.storageSdcardChanged.connect(self._on_storage_target_changed)
        self._bridge.presetSaveRequested.connect(self.on_preset_save_requested)
        self._bridge.presetRecallRequested.connect(self.on_preset_recall_requested)

        self._presets_path = PROJECT_ROOT / "config" / "presets.json"
        self._presets: dict[str, dict] = {}
        self._load_presets()
        self._capture_profile_path = PROJECT_ROOT / "config" / "capture_profile.json"
        self._last_patient_id = ""
        self._load_capture_profile()
        self._load_storage_space_cfg()
        self._on_storage_target_changed(bool(self._bridge.storageSdcard))
        self._bridge.patientIdChanged.connect(self._on_patient_id_changed)
        self._bridge.useLastPatientIdChanged.connect(self._on_use_last_patient_changed)
        self._bridge.autoColorChanged.connect(self._on_bridge_auto_color_changed)
        self._auto_color_gains = np.ones(3, dtype=np.float32)

    # ── Storage target routing (SYSTEM / SD CARD) ───────────────────────────
    def _detect_sd_capture_dir(self) -> Optional[Path]:
        """Return writable SD/removable target directory, else None."""
        if os.name != "nt":
            return None
        try:
            import ctypes
            import string

            get_drive_type = ctypes.windll.kernel32.GetDriveTypeW
            # DRIVE_REMOVABLE = 2
            for letter in string.ascii_uppercase:
                root = f"{letter}:\\"
                if not Path(root).exists():
                    continue
                try:
                    dtype = int(get_drive_type(root))
                except Exception:
                    continue
                if dtype != 2:
                    continue
                target = Path(root) / "DentalImages"
                try:
                    target.mkdir(parents=True, exist_ok=True)
                    probe = target / ".write_test.tmp"
                    probe.write_text("ok", encoding="utf-8")
                    probe.unlink(missing_ok=True)
                    return target
                except Exception:
                    continue
        except Exception:
            return None
        return None

    def _resolved_capture_dir(self) -> Path:
        if bool(self._bridge.storageSdcard):
            sd = self._detect_sd_capture_dir()
            if sd is not None:
                return sd
        return self._system_capture_dir

    def _ensure_snapshot_writer(self) -> bool:
        if not _HAS_SNAPSHOT_WRITER or SnapshotWriter is None:
            self._snapshot_writer = None
            return False
        target_dir = self._resolved_capture_dir()
        if (
            self._snapshot_writer is None
            or Path(self._snapshot_writer.base_directory) != target_dir
        ):
            self._snapshot_writer = SnapshotWriter(target_dir, "png", jpeg_quality=94)
        return True

    @staticmethod
    def _fmt_gib(n_bytes: int) -> str:
        return f"{(max(0, int(n_bytes)) / (1024.0 ** 3)):.2f} GiB"

    def _load_storage_space_cfg(self) -> None:
        defaults = {
            "warn_free_bytes": DEFAULT_STORAGE_WARN_FREE_BYTES,
            "min_capture_free_bytes": DEFAULT_STORAGE_MIN_CAPTURE_FREE_BYTES,
            "estimated_capture_bytes": DEFAULT_ESTIMATED_CAPTURE_BYTES,
        }
        self._storage_space_cfg = dict(defaults)
        try:
            if not STORAGE_CONFIG_PATH.is_file():
                return
            data = json.loads(STORAGE_CONFIG_PATH.read_text(encoding="utf-8"))
            thresholds = data.get("space_thresholds", {})
            if not isinstance(thresholds, dict):
                return
            for key, default_v in defaults.items():
                raw = thresholds.get(key, default_v)
                try:
                    v = int(raw)
                except Exception:
                    v = int(default_v)
                self._storage_space_cfg[key] = max(0, v)
        except Exception:
            self._storage_space_cfg = dict(defaults)

    def _storage_limit(self, key: str, default_v: int) -> int:
        try:
            return max(0, int(self._storage_space_cfg.get(key, default_v)))
        except Exception:
            return int(default_v)

    def _check_capture_storage_space(self) -> bool:
        """
        Guard captures against nearly-full destination media.
        Returns True when capture can continue.
        """
        target_dir = self._resolved_capture_dir()
        try:
            usage = shutil.disk_usage(target_dir)
            free_b = int(usage.free)
        except Exception:
            return True

        required = self._storage_limit("min_capture_free_bytes", DEFAULT_STORAGE_MIN_CAPTURE_FREE_BYTES) + self._storage_limit(
            "estimated_capture_bytes", DEFAULT_ESTIMATED_CAPTURE_BYTES
        )
        if free_b < required:
            self._bridge.toast(
                f"Storage almost full ({self._fmt_gib(free_b)} free). "
                "Free space or switch storage target."
            )
            return False

        now = time.monotonic()
        if free_b < self._storage_limit("warn_free_bytes", DEFAULT_STORAGE_WARN_FREE_BYTES) and (now - self._last_storage_warn_t) > 30.0:
            self._last_storage_warn_t = now
            self._bridge.toast(
                f"Low storage warning: {self._fmt_gib(free_b)} free on capture target."
            )
        return True

    @pyqtSlot(bool)
    def _on_storage_target_changed(self, sdcard: bool) -> None:
        if self._storage_switch_internal:
            return
        sdcard = bool(sdcard)
        if sdcard:
            sd = self._detect_sd_capture_dir()
            if sd is None:
                self._bridge.toast("SD card not detected. Using SYSTEM storage.")
                self._bridge.set_storage_status_text(
                    "Storage: SYSTEM (SD card not detected; fallback active)"
                )
                self._storage_switch_internal = True
                try:
                    self._bridge.onStorageSdcard(False)
                finally:
                    self._storage_switch_internal = False
            else:
                self._bridge.toast(f"Storage target: SD CARD ({sd})")
                self._bridge.set_storage_status_text(f"Storage: SD CARD ({sd})")
        else:
            self._bridge.toast("Storage target: SYSTEM")
            self._bridge.set_storage_status_text(
                f"Storage: SYSTEM ({self._system_capture_dir})"
            )
        self._ensure_snapshot_writer()

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

    # ── Capture profile (patient naming workflow) ───────────────────────────
    def _load_capture_profile(self) -> None:
        self._last_patient_id = ""
        try:
            if self._capture_profile_path.is_file():
                data = json.loads(self._capture_profile_path.read_text(encoding="utf-8"))
                self._last_patient_id = str(data.get("last_patient_id", "")).strip()
                self._bridge.onUseLastPatientId(bool(data.get("use_last_patient_id", True)))
        except Exception:
            self._last_patient_id = ""

        if bool(self._bridge.useLastPatientId) and self._last_patient_id and not str(self._bridge.patientId).strip():
            self._bridge.onPatientIdChanged(self._last_patient_id)

    def _save_capture_profile(self) -> None:
        try:
            self._capture_profile_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "last_patient_id": self._last_patient_id,
                "use_last_patient_id": bool(self._bridge.useLastPatientId),
            }
            self._capture_profile_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    @pyqtSlot(str)
    def _on_patient_id_changed(self, pid: str) -> None:
        pid = str(pid or "").strip()
        if pid:
            self._last_patient_id = pid
        self._save_capture_profile()

    @pyqtSlot(bool)
    def _on_use_last_patient_changed(self, _v: bool) -> None:
        if bool(self._bridge.useLastPatientId) and self._last_patient_id and not str(self._bridge.patientId).strip():
            self._bridge.onPatientIdChanged(self._last_patient_id)
        self._save_capture_profile()

    @staticmethod
    def _sanitize_name(text: str) -> str:
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(text or "").strip())
        return safe.strip("_")

    def _capture_prefix(self, base: str, idx: int = 0) -> str:
        pid = self._sanitize_name(self._bridge.patientId)
        stem = f"{pid}_{base}" if pid else base
        if idx > 0:
            return f"{stem}_{idx:02d}"
        return stem

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
            "autoColor": bool(self._bridge.autoColor),
        }

    @pyqtSlot(int)
    def on_preset_save_requested(self, index: int) -> None:
        k = str(int(index))
        if k not in ("0", "1", "2"):
            return
        self._presets[k] = self._preset_snapshot_from_bridge()
        self._save_presets()
        self._play_capture_sound()
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
        self._stop_burst_internal(silent=True)
        self._capture_delay_timer.stop()
        self._pending_capture_mode = ""
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

    def _on_bridge_auto_color_changed(self, _enabled: bool) -> None:
        # Neutral gains on toggle so the next frames re-learn smoothly from scratch.
        self._auto_color_gains = np.ones(3, dtype=np.float32)

    def _apply_auto_color_stage(self, frame: Optional[np.ndarray]) -> Optional[np.ndarray]:
        if frame is None or frame.size == 0:
            return frame
        if not bool(self._bridge.autoColor):
            return frame
        if (
            not _HAS_COLOR_ADJ
            or compute_auto_color_gains is None
            or apply_auto_color_balance is None
        ):
            return frame
        try:
            target = compute_auto_color_gains(frame)
            self._auto_color_gains = (
                0.8 * self._auto_color_gains + 0.2 * target
            ).astype(np.float32)
            return apply_auto_color_balance(frame, self._auto_color_gains)
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
        frame = self._apply_auto_color_stage(frame)
        if frame is None or frame.size == 0:
            return
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
        """Capture one image, or toggle burst start/stop based on current mode."""
        if self._capture_delay_timer.isActive():
            self._capture_delay_timer.stop()
            self._pending_capture_mode = ""
            self._bridge.toast("Capture cancelled")
            return
        if self._burst_active:
            self._burst_stop_requested = True
            self._bridge.toast("Stopping burst…")
            return
        if self._capture_in_progress:
            return
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            self._bridge.toast("Camera is not connected.")
            return
        if not self._ensure_snapshot_writer() or self._snapshot_writer is None:
            self._bridge.toast("Capture storage is unavailable in this build.")
            return
        if not self._check_capture_storage_space():
            return

        mode = "burst" if bool(self._bridge.captureBurstMode) else "snapshot"
        self._start_capture_with_optional_delay(mode)

    def _start_capture_with_optional_delay(self, mode: str) -> None:
        mode = str(mode or "snapshot").lower()
        if mode not in ("snapshot", "burst"):
            mode = "snapshot"
        delay_s = max(0, int(self._bridge.captureDelaySec))
        if delay_s <= 0:
            self._execute_capture_mode(mode)
            return
        self._pending_capture_mode = mode
        self._capture_delay_timer.start(delay_s * 1000)
        if mode == "burst":
            self._bridge.toast(f"Burst starts in {delay_s}s (tap capture again to cancel)")
        else:
            self._bridge.toast(f"Capture in {delay_s}s (tap capture again to cancel)")

    def _on_capture_delay_elapsed(self) -> None:
        mode = self._pending_capture_mode
        self._pending_capture_mode = ""
        if not mode:
            return
        self._execute_capture_mode(mode)

    def _execute_capture_mode(self, mode: str) -> None:
        if mode == "burst":
            self._start_burst_capture()
            return
        ok, result_name = self._capture_and_save(
            prefix=self._capture_prefix("capture"),
            emit_saved_signal=True
        )
        if ok and result_name:
            self._bridge.toast(f"Saved: {result_name}")

    def _capture_and_save(self, *, prefix: str, emit_saved_signal: bool) -> tuple[bool, str]:
        self._capture_in_progress = True
        try:
            frame = self._camera.grab_still_frame()
            if frame is None or frame.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return False, ""

            frame = self._apply_software_image_adjustments(frame)
            frame = self._apply_auto_color_stage(frame)
            if frame is None or frame.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return False, ""
            cropped, *_ = zoom_crop_pan(
                frame,
                self._bridge.zoom,
                self._bridge.previewPanX,
                self._bridge.previewPanY,
            )
            if cropped is None or cropped.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return False, ""
            out = apply_view_transforms(
                cropped,
                flip_h=self._bridge.flipHorizontal,
                flip_v=self._bridge.flipVertical,
                rotate_q=self._bridge.rotateQuarterTurns,
            )
            if out is None or out.size == 0:
                self._bridge.toast("Capture failed. Please try again.")
                return False, ""

            fmt = "png" if bool(self._bridge.captureFormatPng) else "jpg"
            self._snapshot_writer.set_image_format(fmt)
            self._snapshot_writer.set_jpeg_quality(int(self._bridge.imageQuality))
            result = self._snapshot_writer.save_bgr(out, prefix=prefix)
            self._play_capture_sound()
            try:
                self._bridge.note_capture_saved(str(result.path))
            except Exception:
                pass
            if emit_saved_signal:
                try:
                    self._bridge.captureSaved.emit(str(result.path), int(result.width), int(result.height))
                except Exception:
                    pass
            return True, result.path.name
        except Exception as exc:
            self._bridge.toast(f"Capture failed: {exc}")
            try:
                self._bridge.captureFailed.emit(str(exc))
            except Exception:
                pass
            return False, ""
        finally:
            self._capture_in_progress = False

    def _play_capture_sound(self) -> None:
        if not bool(self._bridge.cameraSoundEnabled):
            return
        # Windows-first subtle feedback; fallback to Qt beep when available.
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_OK)
            return
        except Exception:
            pass
        try:
            from PyQt6.QtGui import QGuiApplication

            QGuiApplication.beep()
        except Exception:
            pass

    def _start_burst_capture(self) -> None:
        self._burst_active = True
        self._burst_stop_requested = False
        self._burst_index = 0
        self._burst_total = max(1, int(self._bridge.captureBurstCount))
        self._bridge.set_burst_state(True, f"Burst 0/{self._burst_total}")
        self._bridge.toast("Burst started. Tap capture again to stop.")
        self._burst_timer.start(0)

    def _stop_burst_internal(self, *, silent: bool = False) -> None:
        if not self._burst_active:
            self._bridge.set_burst_state(False, "")
            return
        self._burst_timer.stop()
        captured = self._burst_index
        self._burst_active = False
        self._burst_stop_requested = False
        self._bridge.set_burst_state(False, "")
        if not silent:
            self._bridge.toast(f"Burst stopped ({captured} captured)")

    def _on_burst_tick(self) -> None:
        if not self._burst_active:
            return
        if self._burst_stop_requested:
            self._stop_burst_internal(silent=False)
            return
        if self._camera is None or not getattr(self._camera, "is_connected", False):
            self._stop_burst_internal(silent=True)
            self._bridge.toast("Burst stopped (camera disconnected)")
            return
        if not self._check_capture_storage_space():
            self._stop_burst_internal(silent=False)
            return

        next_idx = self._burst_index + 1
        ok, _ = self._capture_and_save(
            prefix=self._capture_prefix("burst", idx=next_idx),
            emit_saved_signal=False
        )
        if ok:
            self._burst_index = next_idx
        self._bridge.set_burst_state(True, f"Burst {self._burst_index}/{self._burst_total}")

        if self._burst_stop_requested or self._burst_index >= self._burst_total:
            self._stop_burst_internal(silent=False)
            return

        interval_ms = max(200, int(self._bridge.captureBurstIntervalSec) * 1000)
        self._burst_timer.start(interval_ms)
