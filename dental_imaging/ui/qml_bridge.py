"""
QML ↔ Python bridge.

CameraFrameProvider  – QQuickImageProvider serving BGR→QImage frames to QML
DentalBridge         – QObject exposing all state/controls as QML-accessible
                       properties, signals, and slots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QSize, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtQuick import QQuickImageProvider

if TYPE_CHECKING:
    from dental_imaging.ui.main_window import MainWindow


# ---------------------------------------------------------------------------
# Frame provider (image://camera/frame?<id>)
# ---------------------------------------------------------------------------

class CameraFrameProvider(QQuickImageProvider):
    """Serves the latest processed camera frame to QML as a QImage."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._frame: Optional[QImage] = None
        # Placeholder blank frame
        self._blank = QImage(4, 4, QImage.Format.Format_RGB888)
        self._blank.fill(QColor(0, 0, 0))

    def update_frame(self, frame_bgr: np.ndarray) -> None:
        """Convert numpy BGR frame to QImage and cache it."""
        if frame_bgr is None or frame_bgr.size == 0:
            return
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        # .copy() ensures the buffer is owned (not a slice that gets GC'd)
        self._frame = QImage(
            rgb.data, w, h, w * 3, QImage.Format.Format_RGB888
        ).copy()

    def requestImage(self, id: str, requested_size: QSize):
        """Return (QImage, QSize) so the engine knows the actual frame dimensions.

        PyQt6 collapses the C++ ``QSize *size`` output parameter: the method
        is called with two args (id, requestedSize) and must return a
        ``(QImage, QSize)`` 2-tuple.
        """
        img = self._frame if self._frame is not None else self._blank
        return img, img.size()


# ---------------------------------------------------------------------------
# Main bridge object
# ---------------------------------------------------------------------------

class DentalBridge(QObject):
    """
    Single QObject registered as `bridge` in the QML context.
    All Python→QML state flows through signals / Q_PROPERTYs.
    All QML→Python actions come through @pyqtSlot methods.
    """

    # ── Signals (Python → QML) ─────────────────────────────────────────────
    frameUpdated           = pyqtSignal()          # triggers image source reload
    statsTextChanged       = pyqtSignal(str)
    cameraConnectedChanged = pyqtSignal(bool)
    captureEnabledChanged  = pyqtSignal(bool)
    brightnessChanged      = pyqtSignal(int)
    zoomChanged            = pyqtSignal(int)
    activePresetChanged    = pyqtSignal(int)        # -1 = none
    roiModeActiveChanged   = pyqtSignal(bool)
    autoColorActiveChanged = pyqtSignal(bool)
    imageSettingsChanged   = pyqtSignal('QVariantMap')  # all 7 slider values
    settingsValuesChanged  = pyqtSignal('QVariantMap')  # settings panel state
    toastRequested         = pyqtSignal(str, int)   # message, duration_ms
    statusChanged          = pyqtSignal(str)
    frameIdChanged         = pyqtSignal(int)

    def __init__(self, window: "MainWindow", brand_title: str) -> None:
        super().__init__()
        self._window        = window
        self._brand_title   = brand_title
        self._stats_text    = "— X —     — fps     — MB/s"
        self._connected     = False
        self._capture_en    = False
        self._brightness    = 50
        self._zoom          = 0
        self._active_preset = -1
        self._roi_active    = False
        self._auto_color    = False
        self._frame_id      = 0
        self._status        = "Ready"

    # ── Read-only / notifying properties ───────────────────────────────────

    @pyqtProperty(str, constant=True)
    def brandTitle(self) -> str:
        return self._brand_title

    @pyqtProperty(str, notify=statsTextChanged)
    def statsText(self) -> str:
        return self._stats_text

    @pyqtProperty(bool, notify=cameraConnectedChanged)
    def cameraConnected(self) -> bool:
        return self._connected

    @pyqtProperty(bool, notify=captureEnabledChanged)
    def captureEnabled(self) -> bool:
        return self._capture_en

    @pyqtProperty(int, notify=brightnessChanged)
    def brightness(self) -> int:
        return self._brightness

    @pyqtProperty(int, notify=zoomChanged)
    def zoom(self) -> int:
        return self._zoom

    @pyqtProperty(int, notify=activePresetChanged)
    def activePreset(self) -> int:
        return self._active_preset

    @pyqtProperty(bool, notify=roiModeActiveChanged)
    def roiModeActive(self) -> bool:
        return self._roi_active

    @pyqtProperty(bool, notify=autoColorActiveChanged)
    def autoColorActive(self) -> bool:
        return self._auto_color

    @pyqtProperty(int, notify=frameIdChanged)
    def frameId(self) -> int:
        return self._frame_id

    @pyqtProperty(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    # ── Push helpers (called by MainWindow to update QML) ──────────────────

    def push_frame(self) -> None:
        self._frame_id += 1
        self.frameIdChanged.emit(self._frame_id)
        self.frameUpdated.emit()

    def push_stats(self, text: str) -> None:
        self._stats_text = text
        self.statsTextChanged.emit(text)

    def push_connected(self, connected: bool, capture_enabled: bool) -> None:
        if self._connected != connected:
            self._connected = connected
            self.cameraConnectedChanged.emit(connected)
        if self._capture_en != capture_enabled:
            self._capture_en = capture_enabled
            self.captureEnabledChanged.emit(capture_enabled)

    def push_brightness(self, v: int) -> None:
        if self._brightness != v:
            self._brightness = v
            self.brightnessChanged.emit(v)

    def push_zoom(self, v: int) -> None:
        if self._zoom != v:
            self._zoom = v
            self.zoomChanged.emit(v)

    def push_active_preset(self, index: int) -> None:
        self._active_preset = index
        self.activePresetChanged.emit(index)

    def push_roi_mode(self, active: bool) -> None:
        self._roi_active = active
        self.roiModeActiveChanged.emit(active)

    def push_auto_color(self, active: bool) -> None:
        self._auto_color = active
        self.autoColorActiveChanged.emit(active)

    def push_image_settings(self, values: dict) -> None:
        self.imageSettingsChanged.emit(values)

    def push_settings_values(self, values: dict) -> None:
        self.settingsValuesChanged.emit(values)

    def push_toast(self, message: str, duration_ms: int = 2800) -> None:
        self.toastRequested.emit(message, duration_ms)

    def push_status(self, message: str) -> None:
        self._status = message
        self.statusChanged.emit(message)

    # ── Slots (QML → Python) ───────────────────────────────────────────────

    @pyqtSlot()
    def powerClicked(self) -> None:
        self._window._on_power_clicked()

    @pyqtSlot()
    def flipH(self) -> None:
        self._window._toggle_flip_h()

    @pyqtSlot()
    def flipV(self) -> None:
        self._window._toggle_flip_v()

    @pyqtSlot()
    def rotateCW(self) -> None:
        self._window._rotate_cw()

    @pyqtSlot()
    def rotateCCW(self) -> None:
        self._window._rotate_ccw()

    @pyqtSlot()
    def capture(self) -> None:
        self._window.capture_image()

    @pyqtSlot(bool)
    def autoColorToggled(self, enabled: bool) -> None:
        self._auto_color = enabled
        self._window._on_auto_color_toggled(enabled)

    @pyqtSlot()
    def recenterROI(self) -> None:
        self._window._stub_recenter_roi()

    @pyqtSlot(bool)
    def roiModeToggled(self, enabled: bool) -> None:
        self._roi_active = enabled
        self._window._stub_roi_mode(enabled)

    @pyqtSlot(int)
    def setBrightness(self, v: int) -> None:
        self._brightness = v
        self._window._brightness = v

    @pyqtSlot(int)
    def setZoom(self, v: int) -> None:
        self._zoom = v
        self._window._zoom = v

    @pyqtSlot(int)
    def presetClicked(self, index: int) -> None:
        self._window._on_preset_clicked(index)

    @pyqtSlot(int)
    def presetSaveRequested(self, index: int) -> None:
        self._window._on_preset_save_requested(index)

    # -- Image settings slots --

    @pyqtSlot(result='QVariantMap')
    def getImageSettingsValues(self) -> dict:
        iv = self._window.image_settings.get_values()
        return {
            'exposure':      int(iv.exposure),
            'gain':          int(iv.gain),
            'whiteBalance':  int(iv.white_balance),
            'contrast':      int(iv.contrast),
            'saturation':    int(iv.saturation),
            'warmth':        int(iv.warmth),
            'tint':          int(iv.tint),
        }

    @pyqtSlot(int)
    def setExposure(self, v: int) -> None:
        self._window._camera_auto_exposure = False
        self._window.image_settings.set_exposure_percent(v, block_signals=True)
        self._window._on_image_settings_hardware_push()

    @pyqtSlot(int)
    def setGain(self, v: int) -> None:
        self._window._camera_auto_gain = False
        self._window.image_settings.set_gain_percent(v, block_signals=True)
        self._window._on_image_settings_hardware_push()

    @pyqtSlot(int)
    def setWhiteBalance(self, v: int) -> None:
        self._window.image_settings.set_slider_value("white_balance", v)
        self._window._on_image_settings_hardware_push()

    @pyqtSlot(int)
    def setContrast(self, v: int) -> None:
        self._window.image_settings.set_slider_value("contrast", v)

    @pyqtSlot(int)
    def setSaturation(self, v: int) -> None:
        self._window.image_settings.set_slider_value("saturation", v)

    @pyqtSlot(int)
    def setWarmth(self, v: int) -> None:
        self._window.image_settings.set_slider_value("warmth", v)

    @pyqtSlot(int)
    def setTint(self, v: int) -> None:
        self._window.image_settings.set_slider_value("tint", v)

    @pyqtSlot()
    def resetImageSettings(self) -> None:
        self._window.image_settings.reset_to_defaults()
        iv = self._window.image_settings.get_values()
        self.imageSettingsChanged.emit({
            'exposure':     int(iv.exposure),
            'gain':         int(iv.gain),
            'whiteBalance': int(iv.white_balance),
            'contrast':     int(iv.contrast),
            'saturation':   int(iv.saturation),
            'warmth':       int(iv.warmth),
            'tint':         int(iv.tint),
        })

    # -- Settings panel slots --

    @pyqtSlot(result='QVariantMap')
    def getSettingsValues(self) -> dict:
        w = self._window
        return {
            'showGrid':        bool(w._show_preview_grid),
            'showCrosshair':   bool(w._show_preview_crosshair),
            'autoScale':       bool(w._preview_auto_scale),
            'exportFullRes':   bool(w._export_full_resolution),
            'captureFormat':   str(w._snapshot_writer.image_format),
            'jpegQuality':     int(w._snapshot_writer.jpeg_quality),
            'captureModeBurst': bool(w._burst_capture_mode),
            'burstDelaySec':   int(w._burst_delay_sec),
            'cameraSound':     bool(w._camera_sound_enabled),
            'storageSD':       bool(w._storage_sd_selected),
        }

    @pyqtSlot(bool)
    def setShowGrid(self, v: bool) -> None:
        self._window._on_show_grid_changed(v)

    @pyqtSlot(bool)
    def setShowCrosshair(self, v: bool) -> None:
        self._window._on_show_crosshair_changed(v)

    @pyqtSlot(bool)
    def setAutoScale(self, v: bool) -> None:
        self._window._on_auto_scale_preview_changed(v)

    @pyqtSlot(str)
    def setExportScope(self, scope: str) -> None:
        self._window._on_export_scope_changed(scope)

    @pyqtSlot(str)
    def setCaptureFormat(self, fmt: str) -> None:
        self._window._on_capture_format_changed(fmt)

    @pyqtSlot(int)
    def setJpegQuality(self, q: int) -> None:
        self._window._on_jpeg_quality_changed(q)

    @pyqtSlot(str)
    def setCaptureMode(self, mode: str) -> None:
        self._window._on_capture_mode_changed(mode)

    @pyqtSlot(int)
    def setBurstDelay(self, sec: int) -> None:
        self._window._on_burst_delay_changed(sec)

    @pyqtSlot(bool)
    def setCameraSound(self, v: bool) -> None:
        self._window._on_camera_sound_changed(v)

    @pyqtSlot(str)
    def setStorageTarget(self, t: str) -> None:
        self._window._on_storage_target_changed(t)

    # -- ROI slot --

    @pyqtSlot(float, float, float, float)
    def setROIFromNormalized(self, nx: float, ny: float, nw: float, nh: float) -> None:
        """Receive normalised ROI [0-1] from QML and convert to frame pixels."""
        frame = getattr(self._window, '_current_frame', None)
        if frame is not None:
            fh, fw = frame.shape[:2]
            roi = (
                max(0, int(nx * fw)),
                max(0, int(ny * fh)),
                max(1, int(nw * fw)),
                max(1, int(nh * fh)),
            )
            pw = getattr(self._window, 'preview_widget', None)
            if pw is not None and hasattr(pw, 'set_roi_rect'):
                pw.set_roi_rect(roi)
