"""
DentalBridge — the single Python ↔ QML communication object.

Properties  : Python → QML  (pyqtProperty + notify signal)
Slots       : QML  → Python  (@pyqtSlot)
Action sigs : emitted by slots, connect externally for real behaviour
"""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from urllib.parse import unquote, urlparse

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from runtime_paths import project_root

PROJECT_ROOT = project_root()
STORAGE_CONFIG_PATH = PROJECT_ROOT / "config" / "storage_config.json"
DEFAULT_EXPORT_WARN_FREE_BYTES = 1 * 1024 * 1024 * 1024   # 1 GiB
DEFAULT_EXPORT_RESERVE_BYTES = 128 * 1024 * 1024          # 128 MiB
try:
    import cv2  # type: ignore
    import pydicom  # type: ignore
    from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
    _HAS_DICOM = True
except Exception:
    cv2 = None  # type: ignore
    pydicom = None  # type: ignore
    ExplicitVRLittleEndian = None  # type: ignore
    SecondaryCaptureImageStorage = None  # type: ignore
    generate_uid = None  # type: ignore
    _HAS_DICOM = False


class DentalBridge(QObject):

    # ── Property-change signals ───────────────────────────────────────────────
    connectedChanged            = pyqtSignal(bool)
    statsTextChanged            = pyqtSignal(str)
    frameCounterChanged         = pyqtSignal(int)
    brightnessChanged           = pyqtSignal(int)
    zoomChanged                 = pyqtSignal(int)
    activePresetChanged         = pyqtSignal(int)
    imageSettingsVisibleChanged = pyqtSignal(bool)
    settingsPanelVisibleChanged = pyqtSignal(bool)
    autoColorChanged            = pyqtSignal(bool)
    roiModeChanged              = pyqtSignal(bool)
    capturableChanged           = pyqtSignal(bool)
    exposureChanged             = pyqtSignal(int)
    gainChanged                 = pyqtSignal(int)
    whiteBalanceChanged         = pyqtSignal(int)
    contrastChanged             = pyqtSignal(int)
    saturationChanged           = pyqtSignal(int)
    warmthChanged               = pyqtSignal(int)
    tintChanged                 = pyqtSignal(int)
    showGridOverlayChanged      = pyqtSignal(bool)
    showCrosshairChanged        = pyqtSignal(bool)
    autoScalePreviewChanged     = pyqtSignal(bool)
    captureFormatPngChanged     = pyqtSignal(bool)
    imageQualityChanged         = pyqtSignal(int)
    ledsPresetAutoChanged       = pyqtSignal(bool)
    captureBurstModeChanged     = pyqtSignal(bool)
    burstActiveChanged          = pyqtSignal(bool)
    burstProgressTextChanged    = pyqtSignal(str)
    captureDelaySecChanged      = pyqtSignal(int)
    captureBurstCountChanged    = pyqtSignal(int)
    captureBurstIntervalSecChanged = pyqtSignal(int)
    cameraSoundEnabledChanged   = pyqtSignal(bool)
    storageSdcardChanged        = pyqtSignal(bool)
    camerasDetectedCountChanged = pyqtSignal(int)
    cameraDiscoveryHintChanged  = pyqtSignal(str)
    ledControllerConnectedChanged = pyqtSignal(bool)
    ledControllerPortChanged    = pyqtSignal(str)
    ledControllerStatusTextChanged = pyqtSignal(str)
    storageStatusTextChanged    = pyqtSignal(str)
    patientIdChanged            = pyqtSignal(str)
    useLastPatientIdChanged     = pyqtSignal(bool)
    captureNamePreviewChanged   = pyqtSignal(str)
    settingsUnlockedChanged     = pyqtSignal(bool)
    flipHorizontalChanged       = pyqtSignal(bool)
    flipVerticalChanged         = pyqtSignal(bool)
    rotateQuarterTurnsChanged   = pyqtSignal(int)
    previewPanXChanged          = pyqtSignal(float)
    previewPanYChanged          = pyqtSignal(float)
    minimapViewportXChanged     = pyqtSignal(float)
    minimapViewportYChanged     = pyqtSignal(float)
    minimapViewportWidthChanged = pyqtSignal(float)
    minimapViewportHeightChanged = pyqtSignal(float)
    minimapAspectRatioChanged   = pyqtSignal(float)
    capturePreviewVisibleChanged = pyqtSignal(bool)
    captureItemsChanged         = pyqtSignal()
    capturePreviewIndexChanged  = pyqtSignal(int)

    # ── Action signals (connect from outside for real behaviour) ──────────────
    toastRequested = pyqtSignal(str, arguments=["message"])
    powerClicked   = pyqtSignal()
    captureClicked = pyqtSignal()
    captureSaved   = pyqtSignal(str, int, int, arguments=["path", "width", "height"])
    captureFailed  = pyqtSignal(str, arguments=["message"])
    #: After Image Settings reset — restore camera AE / AGC / AWB (see CameraService).
    imageSettingsDefaultsRestored = pyqtSignal()
    presetRecallRequested = pyqtSignal(int, arguments=["index"])
    presetSaveRequested = pyqtSignal(int, arguments=["index"])
    appExitRequested = pyqtSignal()
    exportAllFolderPickerRequested = pyqtSignal()
    exportAllCompleted = pyqtSignal(
        str, int, int, int, arguments=["folderPath", "exportedCount", "renamedCount", "failedCount"]
    )
    settingsUnlockRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Stream off until CameraService connects
        self._connected          = False
        self._stats_text         = "— × —   — fps   — MB/s"
        self._frame_counter      = 0
        self._brightness         = 26
        self._zoom               = 0
        self._active_preset      = -1
        self._img_settings_vis   = False
        self._settings_panel_vis = False
        self._auto_color         = False
        self._roi_mode           = False
        self._capturable         = False
        self._cameras_detected   = 0
        self._camera_hint        = "Scanning…"
        self._led_connected      = False
        self._led_port           = ""
        self._led_status_text    = "LED controller: reconnecting..."
        self._patient_id         = ""
        self._use_last_patient_id = True
        # Image Settings: 50 = neutral (matches software post-process + reset).
        self._exposure           = 50
        self._gain               = 50
        self._white_balance      = 50
        self._contrast           = 50
        self._saturation         = 50
        self._warmth             = 50
        self._tint               = 50
        self._image_settings_resetting = False
        # Settings modal (reference UI)
        self._show_grid          = False
        self._show_crosshair     = False
        self._auto_scale_preview = False
        self._capture_format_png = True
        self._image_quality      = 94
        self._leds_auto          = True
        self._capture_burst      = False
        self._burst_active       = False
        self._burst_progress     = ""
        self._capture_delay_sec  = 10
        self._capture_burst_count = 10
        self._capture_burst_interval_sec = 2
        self._camera_sound       = False
        self._storage_sdcard     = False
        self._storage_status_text = "Storage: SYSTEM"
        self._flip_h             = False
        self._flip_v             = False
        self._rotate_q           = 0  # 0–3 clockwise quarter turns
        # Zoom pan: 0–1 along axes (0.5 = centred). Minimap: viewport in full-frame norm coords.
        self._pan_x              = 0.5
        self._pan_y              = 0.5
        self._mv_x               = 0.0
        self._mv_y               = 0.0
        self._mv_w               = 1.0
        self._mv_h               = 1.0
        self._minimap_ar         = 1080.0 / 1920.0  # height / width
        self._capture_preview_visible = False
        self._capture_items      = []
        self._capture_preview_index = -1
        self._captures_dir       = project_root() / "captures"
        self._restore_settings_after_preview = False
        self._admin_exit_password = os.environ.get("DENTAL_ADMIN_PASSWORD", "admin")
        self._settings_password = os.environ.get("DENTAL_SETTINGS_PASSWORD", "admin")
        self._settings_unlocked = False
        self._pending_export_mode = "images"  # "images" | "dicom"
        self._storage_space_cfg = {}
        self._load_storage_space_cfg()

    # ── QML-readable properties ───────────────────────────────────────────────
    @pyqtProperty(bool, notify=connectedChanged)
    def connected(self): return self._connected

    @pyqtProperty(str,  notify=statsTextChanged)
    def statsText(self): return self._stats_text

    @pyqtProperty(int,  notify=frameCounterChanged)
    def frameCounter(self): return self._frame_counter

    @pyqtProperty(int,  notify=brightnessChanged)
    def brightness(self): return self._brightness

    @pyqtProperty(int,  notify=zoomChanged)
    def zoom(self): return self._zoom

    @pyqtProperty(int,  notify=activePresetChanged)
    def activePreset(self): return self._active_preset

    @pyqtProperty(bool, notify=imageSettingsVisibleChanged)
    def imageSettingsVisible(self): return self._img_settings_vis

    @pyqtProperty(bool, notify=settingsPanelVisibleChanged)
    def settingsPanelVisible(self): return self._settings_panel_vis

    @pyqtProperty(bool, notify=autoColorChanged)
    def autoColor(self): return self._auto_color

    @pyqtProperty(bool, notify=roiModeChanged)
    def roiMode(self): return self._roi_mode

    @pyqtProperty(bool, notify=capturableChanged)
    def capturable(self): return self._capturable

    @pyqtProperty(int,  notify=exposureChanged)
    def exposure(self): return self._exposure

    @pyqtProperty(int,  notify=gainChanged)
    def gain(self): return self._gain

    @pyqtProperty(int,  notify=whiteBalanceChanged)
    def whiteBalance(self): return self._white_balance

    @pyqtProperty(int,  notify=contrastChanged)
    def contrast(self): return self._contrast

    @pyqtProperty(int,  notify=saturationChanged)
    def saturation(self): return self._saturation

    @pyqtProperty(int,  notify=warmthChanged)
    def warmth(self): return self._warmth

    @pyqtProperty(int,  notify=tintChanged)
    def tint(self): return self._tint

    @pyqtProperty(bool, notify=showGridOverlayChanged)
    def showGridOverlay(self): return self._show_grid

    @pyqtProperty(bool, notify=showCrosshairChanged)
    def showCrosshair(self): return self._show_crosshair

    @pyqtProperty(bool, notify=autoScalePreviewChanged)
    def autoScalePreview(self): return self._auto_scale_preview

    @pyqtProperty(bool, notify=captureFormatPngChanged)
    def captureFormatPng(self): return self._capture_format_png

    @pyqtProperty(int,  notify=imageQualityChanged)
    def imageQuality(self): return self._image_quality

    @pyqtProperty(bool, notify=ledsPresetAutoChanged)
    def ledsPresetAuto(self): return self._leds_auto

    @pyqtProperty(bool, notify=captureBurstModeChanged)
    def captureBurstMode(self): return self._capture_burst

    @pyqtProperty(bool, notify=burstActiveChanged)
    def burstActive(self): return self._burst_active

    @pyqtProperty(str, notify=burstProgressTextChanged)
    def burstProgressText(self): return self._burst_progress

    @pyqtProperty(int,  notify=captureDelaySecChanged)
    def captureDelaySec(self): return self._capture_delay_sec

    @pyqtProperty(int, notify=captureBurstCountChanged)
    def captureBurstCount(self): return self._capture_burst_count

    @pyqtProperty(int, notify=captureBurstIntervalSecChanged)
    def captureBurstIntervalSec(self): return self._capture_burst_interval_sec

    @pyqtProperty(bool, notify=cameraSoundEnabledChanged)
    def cameraSoundEnabled(self): return self._camera_sound

    @pyqtProperty(bool, notify=storageSdcardChanged)
    def storageSdcard(self): return self._storage_sdcard

    @pyqtProperty(int, notify=camerasDetectedCountChanged)
    def camerasDetectedCount(self): return self._cameras_detected

    @pyqtProperty(str, notify=cameraDiscoveryHintChanged)
    def cameraDiscoveryHint(self): return self._camera_hint

    @pyqtProperty(bool, notify=ledControllerConnectedChanged)
    def ledControllerConnected(self): return self._led_connected

    @pyqtProperty(str, notify=ledControllerPortChanged)
    def ledControllerPort(self): return self._led_port

    @pyqtProperty(str, notify=ledControllerStatusTextChanged)
    def ledControllerStatusText(self): return self._led_status_text

    @pyqtProperty(str, notify=storageStatusTextChanged)
    def storageStatusText(self): return self._storage_status_text

    @pyqtProperty(str, notify=patientIdChanged)
    def patientId(self): return self._patient_id

    @pyqtProperty(bool, notify=useLastPatientIdChanged)
    def useLastPatientId(self): return self._use_last_patient_id

    @pyqtProperty(str, notify=captureNamePreviewChanged)
    def captureNamePreview(self):
        fmt = "png" if bool(self._capture_format_png) else "jpg"
        mode = "burst" if bool(self._capture_burst) else "capture"
        pid = self._sanitize_name(self._patient_id)
        base = f"{pid}_{mode}" if pid else mode
        return f"{base}_YYYYMMDD_HHMMSS.{fmt}"

    @pyqtProperty(bool, notify=settingsUnlockedChanged)
    def settingsUnlocked(self): return self._settings_unlocked

    @pyqtProperty(bool, notify=flipHorizontalChanged)
    def flipHorizontal(self): return self._flip_h

    @pyqtProperty(bool, notify=flipVerticalChanged)
    def flipVertical(self): return self._flip_v

    @pyqtProperty(int, notify=rotateQuarterTurnsChanged)
    def rotateQuarterTurns(self): return self._rotate_q

    @pyqtProperty(float, notify=previewPanXChanged)
    def previewPanX(self): return self._pan_x

    @pyqtProperty(float, notify=previewPanYChanged)
    def previewPanY(self): return self._pan_y

    @pyqtProperty(float, notify=minimapViewportXChanged)
    def minimapViewportX(self): return self._mv_x

    @pyqtProperty(float, notify=minimapViewportYChanged)
    def minimapViewportY(self): return self._mv_y

    @pyqtProperty(float, notify=minimapViewportWidthChanged)
    def minimapViewportWidth(self): return self._mv_w

    @pyqtProperty(float, notify=minimapViewportHeightChanged)
    def minimapViewportHeight(self): return self._mv_h

    @pyqtProperty(float, notify=minimapAspectRatioChanged)
    def minimapAspectRatio(self): return self._minimap_ar

    @pyqtProperty(bool, notify=capturePreviewVisibleChanged)
    def capturePreviewVisible(self): return self._capture_preview_visible

    @pyqtProperty("QVariantList", notify=captureItemsChanged)
    def captureItems(self): return self._capture_items

    @pyqtProperty(int, notify=capturePreviewIndexChanged)
    def capturePreviewIndex(self): return self._capture_preview_index

    # ── Python-side setters (called by backend) ───────────────────────────────
    def set_connected(self, v):
        if self._connected != v:
            self._connected = v; self.connectedChanged.emit(v)

    def set_stats(self, w, h, fps, mbps):
        if w <= 0 or h <= 0:
            t = "— × —   — fps   — MB/s"
        else:
            t = f"{w} × {h}   {fps:.0f} fps   {mbps:.1f} MB/s"
        if self._stats_text != t:
            self._stats_text = t
            self.statsTextChanged.emit(t)

    def clear_stream_stats(self):
        self.set_stats(0, 0, 0, 0)

    def set_camera_detection(self, count: int, summary: str):
        if self._cameras_detected != count:
            self._cameras_detected = count
            self.camerasDetectedCountChanged.emit(count)
        if self._camera_hint != summary:
            self._camera_hint = summary
            self.cameraDiscoveryHintChanged.emit(summary)

    def set_led_controller_state(self, connected: bool, port: str = "") -> None:
        connected = bool(connected)
        port = str(port or "")
        if self._led_connected != connected:
            self._led_connected = connected
            self.ledControllerConnectedChanged.emit(connected)
        if self._led_port != port:
            self._led_port = port
            self.ledControllerPortChanged.emit(port)
        if connected:
            self.set_led_controller_status_text(f"LED controller: connected ({port})")
        elif port:
            self.set_led_controller_status_text(f"LED controller: disconnected ({port})")
        else:
            self.set_led_controller_status_text("LED controller: reconnecting...")

    def set_led_controller_status_text(self, text: str) -> None:
        text = str(text or "").strip()
        if not text:
            text = "LED controller: reconnecting..."
        if self._led_status_text != text:
            self._led_status_text = text
            self.ledControllerStatusTextChanged.emit(text)

    def set_storage_status_text(self, text: str) -> None:
        text = str(text or "").strip()
        if not text:
            text = "Storage: SYSTEM"
        if self._storage_status_text != text:
            self._storage_status_text = text
            self.storageStatusTextChanged.emit(text)

    def _refresh_capture_items(self, select_path: str = "") -> None:
        files = []
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        if self._captures_dir.is_dir():
            for p in self._captures_dir.iterdir():
                if p.is_file() and p.suffix.lower() in exts:
                    try:
                        mtime = p.stat().st_mtime
                    except Exception:
                        mtime = 0.0
                    files.append((mtime, p))
        files.sort(key=lambda t: t[0], reverse=True)

        old_len = len(self._capture_items)
        self._capture_items = []
        for mtime, p in files:
            self._capture_items.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "url": p.resolve().as_uri(),
                    "datetime": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "mtime": float(mtime),
                }
            )

        idx = -1
        if select_path:
            for i, item in enumerate(self._capture_items):
                if str(item.get("path", "")) == str(select_path):
                    idx = i
                    break
        if idx < 0 and self._capture_items:
            idx = 0
        self._set_capture_preview_index(idx)
        if old_len != len(self._capture_items) or old_len > 0 or len(self._capture_items) > 0:
            self.captureItemsChanged.emit()

    def _set_capture_preview_index(self, idx: int) -> None:
        n = len(self._capture_items)
        if n <= 0:
            idx = -1
        else:
            idx = max(0, min(n - 1, int(idx)))
        if self._capture_preview_index != idx:
            self._capture_preview_index = idx
            self.capturePreviewIndexChanged.emit(idx)

    def note_capture_saved(self, path: str) -> None:
        self._refresh_capture_items(select_path=path)

    def push_frame(self, _provider=None):
        """Call after provider.update_frame(); increments the QML image URL counter."""
        self._frame_counter += 1
        self.frameCounterChanged.emit(self._frame_counter)

    def set_capturable(self, v: bool):
        v = bool(v)
        if self._capturable != v:
            self._capturable = v
            self.capturableChanged.emit(v)

    def set_burst_state(self, active: bool, progress_text: str = "") -> None:
        active = bool(active)
        progress_text = str(progress_text or "")
        if self._burst_active != active:
            self._burst_active = active
            self.burstActiveChanged.emit(active)
        if self._burst_progress != progress_text:
            self._burst_progress = progress_text
            self.burstProgressTextChanged.emit(progress_text)

    def set_brightness(self, v):
        v = max(0, min(100, v))
        if self._brightness != v:
            self._brightness = v; self.brightnessChanged.emit(v)

    @staticmethod
    def _sanitize_name(text: str) -> str:
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(text or "").strip())
        return safe.strip("_")

    def set_zoom(self, v):
        v = max(0, min(100, int(v)))
        if self._zoom == v:
            return
        self._zoom = v
        self.zoomChanged.emit(v)
        if v <= 2:
            self._reset_preview_pan()

    def _reset_preview_pan(self) -> None:
        if self._pan_x != 0.5:
            self._pan_x = 0.5
            self.previewPanXChanged.emit(self._pan_x)
        if self._pan_y != 0.5:
            self._pan_y = 0.5
            self.previewPanYChanged.emit(self._pan_y)

    def reset_live_view_navigation(self) -> None:
        """Disconnected / placeholder — centre pan and full-frame minimap rect."""
        self._reset_preview_pan()
        self._set_minimap_viewport_rect(0.0, 0.0, 1.0, 1.0)
        self._minimap_ar = 1080.0 / 1920.0
        self.minimapAspectRatioChanged.emit(self._minimap_ar)

    def _set_minimap_viewport_rect(self, vx: float, vy: float, vw: float, vh: float) -> None:
        vx, vy = max(0.0, min(1.0, float(vx))), max(0.0, min(1.0, float(vy)))
        vw, vh = max(0.0, min(1.0, float(vw))), max(0.0, min(1.0, float(vh)))
        if self._mv_x != vx:
            self._mv_x = vx
            self.minimapViewportXChanged.emit(vx)
        if self._mv_y != vy:
            self._mv_y = vy
            self.minimapViewportYChanged.emit(vy)
        if self._mv_w != vw:
            self._mv_w = vw
            self.minimapViewportWidthChanged.emit(vw)
        if self._mv_h != vh:
            self._mv_h = vh
            self.minimapViewportHeightChanged.emit(vh)

    def update_minimap_from_crop(
        self, x0: int, y0: int, cw: int, ch: int, fw: int, fh: int
    ) -> None:
        if fw <= 0 or fh <= 0:
            return
        self._minimap_ar = float(fh) / float(fw)
        self.minimapAspectRatioChanged.emit(self._minimap_ar)
        self._set_minimap_viewport_rect(
            x0 / float(fw), y0 / float(fh), cw / float(fw), ch / float(fh)
        )

    def set_active_preset(self, idx):
        if self._active_preset != idx:
            self._active_preset = idx; self.activePresetChanged.emit(idx)

    def set_auto_color(self, v):
        if self._auto_color != v:
            self._auto_color = v; self.autoColorChanged.emit(v)

    def set_roi_mode(self, v):
        if self._roi_mode != v:
            self._roi_mode = v
            self.roiModeChanged.emit(v)
            if v:
                self.toast("ROI mode enabled. Drag diagonally to select.")
            else:
                self.toast("ROI mode disabled")

    def toast(self, msg):
        self.toastRequested.emit(msg)

    # ── QML slots ─────────────────────────────────────────────────────────────
    @pyqtSlot()
    def onPowerClicked(self): self.powerClicked.emit()

    @pyqtSlot()
    def onCapture(self):
        if not self._capturable:
            self.toast("Connect the camera to capture")
            return
        self.captureClicked.emit()

    @pyqtSlot(bool)
    def onImageSettingsToggled(self, v):
        self._img_settings_vis = v
        self.imageSettingsVisibleChanged.emit(v)
        if v and self._settings_panel_vis:
            self._settings_panel_vis = False
            self.settingsPanelVisibleChanged.emit(False)

    @pyqtSlot(bool)
    def onSettingsPanelToggled(self, v):
        if v and not self._settings_unlocked:
            self.settingsUnlockRequested.emit()
            return
        self._settings_panel_vis = v
        self.settingsPanelVisibleChanged.emit(v)
        if v and self._img_settings_vis:
            self._img_settings_vis = False
            self.imageSettingsVisibleChanged.emit(False)

    @pyqtSlot(int)
    def onBrightnessChanged(self, v): self.set_brightness(v)

    @pyqtSlot(int)
    def onZoomChanged(self, v): self.set_zoom(v)

    @pyqtSlot(float, float, float, float)
    def applyPreviewPanDelta(self, dx, dy, view_w, view_h):
        """Drag on preview while zoomed: move crop (phone-style)."""
        if self._zoom <= 2 or view_w <= 1.0 or view_h <= 1.0:
            return
        k = 1.65
        nx = self._pan_x - (float(dx) / float(view_w)) * k
        ny = self._pan_y - (float(dy) / float(view_h)) * k
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        if nx != self._pan_x:
            self._pan_x = nx
            self.previewPanXChanged.emit(nx)
        if ny != self._pan_y:
            self._pan_y = ny
            self.previewPanYChanged.emit(ny)

    @pyqtSlot()
    def resetPreviewPan(self):
        """Re-centre the zoomed crop (double-tap / shortcut)."""
        self._reset_preview_pan()

    @pyqtSlot(float, float)
    def setPreviewPanFromMinimap(self, nx, ny):
        """Jump/drag pan target from minimap normalized coordinates [0..1]."""
        if self._zoom <= 2:
            return
        nx = max(0.0, min(1.0, float(nx)))
        ny = max(0.0, min(1.0, float(ny)))
        if nx != self._pan_x:
            self._pan_x = nx
            self.previewPanXChanged.emit(nx)
        if ny != self._pan_y:
            self._pan_y = ny
            self.previewPanYChanged.emit(ny)

    @pyqtSlot(float, float, float, float)
    def applyRoiSelection(self, x0n, y0n, x1n, y1n):
        """
        Apply ROI box (normalized preview coords) as zoom+pan target.
        Release-to-apply: centers selected region and scales zoom to fit it.
        """
        x0 = max(0.0, min(1.0, float(x0n)))
        y0 = max(0.0, min(1.0, float(y0n)))
        x1 = max(0.0, min(1.0, float(x1n)))
        y1 = max(0.0, min(1.0, float(y1n)))

        lx, rx = (x0, x1) if x0 <= x1 else (x1, x0)
        ty, by = (y0, y1) if y0 <= y1 else (y1, y0)
        rw = rx - lx
        rh = by - ty
        if rw < 0.02 or rh < 0.02:
            self.toast("ROI area too small")
            return

        # Existing zoom model uses crop fraction f = 1 - 0.7 * (zoom/100).
        fit_frac = max(rw, rh)
        t = (1.0 - fit_frac) / 0.7
        zoom = int(round(max(0.0, min(1.0, t)) * 100.0))
        zoom = max(3, zoom)
        self.set_zoom(zoom)

        cx = (lx + rx) * 0.5
        cy = (ty + by) * 0.5
        if cx != self._pan_x:
            self._pan_x = cx
            self.previewPanXChanged.emit(cx)
        if cy != self._pan_y:
            self._pan_y = cy
            self.previewPanYChanged.emit(cy)

        if self._roi_mode:
            self._roi_mode = False
            self.roiModeChanged.emit(False)
        self.toast("ROI applied")

    @pyqtSlot(int)
    def onPresetClicked(self, idx):
        if self._active_preset == idx:
            self.set_active_preset(-1)
            return
        self.set_active_preset(idx)
        self.presetRecallRequested.emit(idx)

    @pyqtSlot(int)
    def onPresetSave(self, idx):
        self.presetSaveRequested.emit(idx)

    # ── Preset apply helper (called by backend) ───────────────────────────────
    def apply_preset_snapshot(self, snap: dict) -> None:
        """Apply a preset snapshot dict onto bridge state and notify QML."""
        if not isinstance(snap, dict):
            return

        def _i(key: str, lo: int, hi: int, cur: int, sig) -> int:
            try:
                v = int(snap.get(key, cur))
            except Exception:
                v = cur
            v = max(lo, min(hi, v))
            if v != cur:
                sig.emit(v)
            return v

        def _b(key: str, cur: bool, sig) -> bool:
            v = bool(snap.get(key, cur))
            if v != cur:
                sig.emit(v)
            return v

        # Sliders / basic
        self._brightness = _i("brightness", 0, 100, self._brightness, self.brightnessChanged)
        self.set_zoom(_i("zoom", 0, 100, self._zoom, self.zoomChanged))

        # Pan (normalized) — apply only when zoom is active.
        try:
            px = float(snap.get("previewPanX", self._pan_x))
            py = float(snap.get("previewPanY", self._pan_y))
            px = max(0.0, min(1.0, px))
            py = max(0.0, min(1.0, py))
            if self._zoom > 2:
                if px != self._pan_x:
                    self._pan_x = px
                    self.previewPanXChanged.emit(px)
                if py != self._pan_y:
                    self._pan_y = py
                    self.previewPanYChanged.emit(py)
        except Exception:
            pass

        # View transforms
        self._flip_h = _b("flipHorizontal", self._flip_h, self.flipHorizontalChanged)
        self._flip_v = _b("flipVertical", self._flip_v, self.flipVerticalChanged)
        self._rotate_q = _i("rotateQuarterTurns", 0, 3, self._rotate_q, self.rotateQuarterTurnsChanged)

        # Image settings (0–100, 50 neutral)
        self._exposure = _i("exposure", 0, 100, self._exposure, self.exposureChanged)
        self._gain = _i("gain", 0, 100, self._gain, self.gainChanged)
        self._white_balance = _i("whiteBalance", 0, 100, self._white_balance, self.whiteBalanceChanged)
        self._contrast = _i("contrast", 0, 100, self._contrast, self.contrastChanged)
        self._saturation = _i("saturation", 0, 100, self._saturation, self.saturationChanged)
        self._warmth = _i("warmth", 0, 100, self._warmth, self.warmthChanged)
        self._tint = _i("tint", 0, 100, self._tint, self.tintChanged)

        # Capture prefs
        self._capture_format_png = _b("captureFormatPng", self._capture_format_png, self.captureFormatPngChanged)
        self._image_quality = _i("imageQuality", 1, 100, self._image_quality, self.imageQualityChanged)
        self._auto_color = _b("autoColor", self._auto_color, self.autoColorChanged)

    @pyqtSlot(bool)
    def onAutoColorToggled(self, v):
        self.set_auto_color(v)
        self.toast("Auto colour ON" if v else "Auto colour OFF")

    @pyqtSlot(bool)
    def onRoiModeToggled(self, v): self.set_roi_mode(v)

    @pyqtSlot()
    def onRecenterRoi(self):
        self._reset_preview_pan()
        self.toast("ROI recentered")

    @pyqtSlot()
    def onFlipH(self):
        self._flip_h = not self._flip_h
        self.flipHorizontalChanged.emit(self._flip_h)

    @pyqtSlot()
    def onFlipV(self):
        self._flip_v = not self._flip_v
        self.flipVerticalChanged.emit(self._flip_v)

    @pyqtSlot()
    def onRotateCw(self):
        self._rotate_q = (self._rotate_q + 1) % 4
        self.rotateQuarterTurnsChanged.emit(self._rotate_q)

    @pyqtSlot()
    def onRotateCcw(self):
        self._rotate_q = (self._rotate_q - 1) % 4
        self.rotateQuarterTurnsChanged.emit(self._rotate_q)

    @pyqtSlot(int)
    def onExposureChanged(self, v):
        if self._exposure != v: self._exposure = v; self.exposureChanged.emit(v)

    @pyqtSlot(int)
    def onGainChanged(self, v):
        if self._gain != v: self._gain = v; self.gainChanged.emit(v)

    @pyqtSlot(int)
    def onWhiteBalanceChanged(self, v):
        if self._white_balance != v: self._white_balance = v; self.whiteBalanceChanged.emit(v)

    @pyqtSlot(int)
    def onContrastChanged(self, v):
        if self._contrast != v: self._contrast = v; self.contrastChanged.emit(v)

    @pyqtSlot(int)
    def onSaturationChanged(self, v):
        if self._saturation != v: self._saturation = v; self.saturationChanged.emit(v)

    @pyqtSlot(int)
    def onWarmthChanged(self, v):
        if self._warmth != v: self._warmth = v; self.warmthChanged.emit(v)

    @pyqtSlot(int)
    def onTintChanged(self, v):
        if self._tint != v: self._tint = v; self.tintChanged.emit(v)

    @pyqtSlot()
    def onImageSettingsReset(self):
        self._image_settings_resetting = True
        try:
            for attr in ("_exposure", "_gain", "_white_balance", "_contrast",
                         "_saturation", "_warmth", "_tint"):
                setattr(self, attr, 50)
            for sig in (self.exposureChanged, self.gainChanged, self.whiteBalanceChanged,
                        self.contrastChanged, self.saturationChanged,
                        self.warmthChanged, self.tintChanged):
                sig.emit(50)
            self.toast("Settings reset to defaults")
        finally:
            self._image_settings_resetting = False
        self.imageSettingsDefaultsRestored.emit()

    # ── Settings modal slots ──────────────────────────────────────────────────
    @pyqtSlot(bool)
    def onShowGridOverlayToggled(self, v):
        if self._show_grid != v:
            self._show_grid = v
            self.showGridOverlayChanged.emit(v)

    @pyqtSlot(bool)
    def onShowCrosshairToggled(self, v):
        if self._show_crosshair != v:
            self._show_crosshair = v
            self.showCrosshairChanged.emit(v)

    @pyqtSlot(bool)
    def onAutoScalePreviewToggled(self, v):
        if self._auto_scale_preview != v:
            self._auto_scale_preview = v
            self.autoScalePreviewChanged.emit(v)

    @pyqtSlot(bool)
    def onCaptureFormatPng(self, png):
        png = bool(png)
        if self._capture_format_png == png:
            return
        self._capture_format_png = png
        self.captureFormatPngChanged.emit(png)
        self.captureNamePreviewChanged.emit(self.captureNamePreview)
        self.toast("Capture format: PNG" if png else "Capture format: JPG")

    @pyqtSlot(bool)
    def onLedsPresetAuto(self, auto_on):
        auto_on = bool(auto_on)
        if self._leds_auto == auto_on:
            return
        self._leds_auto = auto_on
        self.ledsPresetAutoChanged.emit(auto_on)
        self.toast("LED preset: AUTO" if auto_on else "LED preset: MANUAL")

    @pyqtSlot(str)
    def onLedsPresetManual(self, preset):
        p = str(preset or "").strip().lower()
        if p not in ("off", "high"):
            return
        self.onLedsPresetAuto(False)
        target = 0 if p == "off" else 100
        self.set_brightness(target)
        self.toast("LED preset: OFF" if target == 0 else "LED preset: HIGH")

    @pyqtSlot(bool)
    def onCaptureBurstMode(self, burst):
        burst = bool(burst)
        if self._capture_burst == burst:
            return
        self._capture_burst = burst
        self.captureBurstModeChanged.emit(burst)
        self.captureNamePreviewChanged.emit(self.captureNamePreview)
        self.toast("Capture mode: BURST" if burst else "Capture mode: SNAPSHOT")

    @pyqtSlot(int)
    def onCaptureDelaySec(self, sec):
        if self._capture_delay_sec != sec:
            self._capture_delay_sec = sec
            self.captureDelaySecChanged.emit(sec)

    @pyqtSlot(int)
    def onCaptureBurstCount(self, count):
        count = max(1, min(99, int(count)))
        if self._capture_burst_count != count:
            self._capture_burst_count = count
            self.captureBurstCountChanged.emit(count)

    @pyqtSlot(int)
    def onCaptureBurstIntervalSec(self, sec):
        sec = max(1, min(600, int(sec)))
        if self._capture_burst_interval_sec != sec:
            self._capture_burst_interval_sec = sec
            self.captureBurstIntervalSecChanged.emit(sec)

    @pyqtSlot(bool)
    def onCameraSoundToggled(self, v):
        if self._camera_sound != v:
            self._camera_sound = v
            self.cameraSoundEnabledChanged.emit(v)

    @pyqtSlot(bool)
    def onStorageSdcard(self, sdcard):
        if self._storage_sdcard != sdcard:
            self._storage_sdcard = sdcard
            self.storageSdcardChanged.emit(sdcard)

    @pyqtSlot(str)
    def onPatientIdChanged(self, pid):
        pid = str(pid or "").strip()
        if self._patient_id != pid:
            self._patient_id = pid
            self.patientIdChanged.emit(pid)
            self.captureNamePreviewChanged.emit(self.captureNamePreview)

    @pyqtSlot(bool)
    def onUseLastPatientId(self, use_last):
        use_last = bool(use_last)
        if self._use_last_patient_id != use_last:
            self._use_last_patient_id = use_last
            self.useLastPatientIdChanged.emit(use_last)

    @pyqtSlot()
    def onExportAllClicked(self):
        self._pending_export_mode = "images"
        self.exportAllFolderPickerRequested.emit()

    @pyqtSlot()
    def onExportDicomClicked(self):
        self._pending_export_mode = "dicom"
        self.exportAllFolderPickerRequested.emit()

    def _decode_folder_input(self, folder: str) -> Path:
        raw = str(folder or "").strip()
        if not raw:
            return Path()
        # Handle FolderDialog URL form: file:///C:/...
        if raw.startswith("file:"):
            p = urlparse(raw)
            path = unquote(p.path or "")
            # Windows: /C:/Users/... -> C:/Users/...
            if len(path) >= 3 and path[0] == "/" and path[2] == ":":
                path = path[1:]
            return Path(path)
        return Path(raw)

    @staticmethod
    def _fmt_gib(n_bytes: int) -> str:
        return f"{(max(0, int(n_bytes)) / (1024.0 ** 3)):.2f} GiB"

    def _load_storage_space_cfg(self) -> None:
        defaults = {
            "export_warn_free_bytes": DEFAULT_EXPORT_WARN_FREE_BYTES,
            "export_reserve_bytes": DEFAULT_EXPORT_RESERVE_BYTES,
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

    @pyqtSlot(str)
    def onExportAllToFolder(self, folder):
        # Reload on each export so config tweaks apply without restart.
        self._load_storage_space_cfg()
        self._refresh_capture_items()
        if not self._capture_items:
            self.toast("No captured images to export")
            return

        dst = self._decode_folder_input(str(folder))
        if not str(dst):
            self.toast("Export cancelled")
            return

        try:
            dst.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.toast(f"Export failed: {exc}")
            return

        # Preflight disk-space check: source total + 128 MiB reserve.
        try:
            total_src_bytes = 0
            for item in self._capture_items:
                src = Path(str(item.get("path", "")))
                if src.is_file():
                    total_src_bytes += int(src.stat().st_size)
            reserve_bytes = self._storage_limit("export_reserve_bytes", DEFAULT_EXPORT_RESERVE_BYTES)
            usage = shutil.disk_usage(dst)
            free_b = int(usage.free)
            need_b = int(total_src_bytes + reserve_bytes)
            if free_b < need_b:
                self.toast(
                    f"Export blocked: not enough space ({self._fmt_gib(free_b)} free, "
                    f"{self._fmt_gib(need_b)} required)."
                )
                return
            if free_b < self._storage_limit("export_warn_free_bytes", DEFAULT_EXPORT_WARN_FREE_BYTES):
                self.toast(f"Low storage warning on export target: {self._fmt_gib(free_b)} free")
        except Exception:
            # If we cannot read usage metadata, proceed with best effort.
            pass

        ok = 0
        renamed = 0
        failed = 0
        if self._pending_export_mode == "dicom":
            self._export_dicom_to_folder(dst)
            return
        for item in self._capture_items:
            src = Path(str(item.get("path", "")))
            if not src.is_file():
                failed += 1
                continue
            target = dst / src.name
            if target.exists():
                stem = src.stem
                suf = src.suffix
                i = 1
                while True:
                    cand = dst / f"{stem}_{i}{suf}"
                    if not cand.exists():
                        target = cand
                        renamed += 1
                        break
                    i += 1
            try:
                shutil.copy2(src, target)
                ok += 1
            except Exception:
                failed += 1

        if failed == 0:
            self.toast(f"Export complete: {ok} files")
        else:
            self.toast(f"Export complete: {ok} ok, {failed} failed")
        try:
            self.exportAllCompleted.emit(str(dst), int(ok), int(renamed), int(failed))
        except Exception:
            pass

    def _export_dicom_to_folder(self, dst: Path) -> None:
        if not _HAS_DICOM or cv2 is None or pydicom is None or generate_uid is None:
            self.toast("DICOM export unavailable: install pydicom and opencv-python")
            return
        ok = 0
        failed = 0
        for item in self._capture_items:
            src = Path(str(item.get("path", "")))
            if not src.is_file():
                failed += 1
                continue
            try:
                img = cv2.imread(str(src), cv2.IMREAD_COLOR)
                if img is None or img.size == 0:
                    failed += 1
                    continue
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]

                file_meta = pydicom.dataset.FileMetaDataset()
                file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
                file_meta.MediaStorageSOPInstanceUID = generate_uid()
                file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                file_meta.ImplementationClassUID = generate_uid()

                ds = pydicom.dataset.FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
                now = datetime.now()
                ds.Modality = "XC"
                ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
                ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
                ds.StudyInstanceUID = generate_uid()
                ds.SeriesInstanceUID = generate_uid()
                ds.PatientName = str(self._patient_id or "Unknown")
                ds.PatientID = str(self._patient_id or "UNKNOWN")
                ds.StudyDate = now.strftime("%Y%m%d")
                ds.StudyTime = now.strftime("%H%M%S")
                ds.ContentDate = now.strftime("%Y%m%d")
                ds.ContentTime = now.strftime("%H%M%S")
                ds.Rows = h
                ds.Columns = w
                ds.SamplesPerPixel = 3
                ds.PhotometricInterpretation = "RGB"
                ds.PlanarConfiguration = 0
                ds.BitsAllocated = 8
                ds.BitsStored = 8
                ds.HighBit = 7
                ds.PixelRepresentation = 0
                ds.PixelData = rgb.tobytes()
                ds.is_little_endian = True
                ds.is_implicit_VR = False

                out_path = dst / f"{src.stem}.dcm"
                i = 1
                while out_path.exists():
                    out_path = dst / f"{src.stem}_{i}.dcm"
                    i += 1
                ds.save_as(str(out_path), write_like_original=False)
                ok += 1
            except Exception:
                failed += 1

        if failed == 0:
            self.toast(f"DICOM export complete: {ok} files")
        else:
            self.toast(f"DICOM export complete: {ok} ok, {failed} failed")
        try:
            self.exportAllCompleted.emit(str(dst), int(ok), 0, int(failed))
        except Exception:
            pass

    @pyqtSlot(str)
    def onRequestAppExit(self, password):
        if str(password or "") == self._admin_exit_password:
            self.appExitRequested.emit()
        else:
            self.toast("Invalid admin password")

    @pyqtSlot(str)
    def onRequestSettingsUnlock(self, password):
        if str(password or "") == self._settings_password:
            if not self._settings_unlocked:
                self._settings_unlocked = True
                self.settingsUnlockedChanged.emit(True)
            self._settings_panel_vis = True
            self.settingsPanelVisibleChanged.emit(True)
            if self._img_settings_vis:
                self._img_settings_vis = False
                self.imageSettingsVisibleChanged.emit(False)
        else:
            self.toast("Invalid settings password")

    @pyqtSlot()
    def onLockSettingsPanel(self):
        if self._settings_unlocked:
            self._settings_unlocked = False
            self.settingsUnlockedChanged.emit(False)
        if self._settings_panel_vis:
            self._settings_panel_vis = False
            self.settingsPanelVisibleChanged.emit(False)
        self.toast("Settings locked")

    @pyqtSlot()
    def onCapturePreviewOpen(self):
        self._refresh_capture_items()
        if not self._capture_items:
            self.toast("No captured images found")
            return
        # Capture Preview takes focus; remember whether settings was open.
        self._restore_settings_after_preview = bool(self._settings_panel_vis)
        if self._settings_panel_vis:
            self._settings_panel_vis = False
            self.settingsPanelVisibleChanged.emit(False)
        if not self._capture_preview_visible:
            self._capture_preview_visible = True
            self.capturePreviewVisibleChanged.emit(True)

    @pyqtSlot()
    def onCapturePreviewClose(self):
        if self._capture_preview_visible:
            self._capture_preview_visible = False
            self.capturePreviewVisibleChanged.emit(False)
        if self._restore_settings_after_preview and not self._settings_panel_vis:
            self._settings_panel_vis = True
            self.settingsPanelVisibleChanged.emit(True)
        self._restore_settings_after_preview = False

    @pyqtSlot()
    def onCapturePreviewRefresh(self):
        self._refresh_capture_items()

    @pyqtSlot(int)
    def onCapturePreviewSelect(self, idx):
        self._set_capture_preview_index(int(idx))

    @pyqtSlot()
    def onCapturePreviewNext(self):
        if not self._capture_items:
            return
        self._set_capture_preview_index(self._capture_preview_index + 1)

    @pyqtSlot()
    def onCapturePreviewPrevious(self):
        if not self._capture_items:
            return
        self._set_capture_preview_index(self._capture_preview_index - 1)
