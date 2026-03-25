"""
DentalBridge — the single Python ↔ QML communication object.

Properties  : Python → QML  (pyqtProperty + notify signal)
Slots       : QML  → Python  (@pyqtSlot)
Action sigs : emitted by slots, connect externally for real behaviour
"""
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot


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
    captureDelaySecChanged      = pyqtSignal(int)
    cameraSoundEnabledChanged   = pyqtSignal(bool)
    storageSdcardChanged        = pyqtSignal(bool)
    camerasDetectedCountChanged = pyqtSignal(int)
    cameraDiscoveryHintChanged  = pyqtSignal(str)

    # ── Action signals (connect from outside for real behaviour) ──────────────
    toastRequested = pyqtSignal(str, arguments=["message"])
    powerClicked   = pyqtSignal()
    captureClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Stream off until CameraService connects
        self._connected          = False
        self._stats_text         = "— × —   — fps   — MB/s"
        self._frame_counter      = 0
        self._brightness         = 26
        self._zoom               = 26
        self._active_preset      = -1
        self._img_settings_vis   = False
        self._settings_panel_vis = False
        self._auto_color         = False
        self._roi_mode           = False
        self._capturable         = False
        self._cameras_detected   = 0
        self._camera_hint        = "Scanning…"
        self._exposure           = 26
        self._gain               = 26
        self._white_balance      = 26
        self._contrast           = 26
        self._saturation         = 26
        self._warmth             = 26
        self._tint               = 26
        # Settings modal (reference UI)
        self._show_grid          = False
        self._show_crosshair     = False
        self._auto_scale_preview = False
        self._capture_format_png = True
        self._image_quality      = 94
        self._leds_auto          = True
        self._capture_burst      = True
        self._capture_delay_sec  = 10
        self._camera_sound       = False
        self._storage_sdcard     = False

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

    @pyqtProperty(int,  notify=captureDelaySecChanged)
    def captureDelaySec(self): return self._capture_delay_sec

    @pyqtProperty(bool, notify=cameraSoundEnabledChanged)
    def cameraSoundEnabled(self): return self._camera_sound

    @pyqtProperty(bool, notify=storageSdcardChanged)
    def storageSdcard(self): return self._storage_sdcard

    @pyqtProperty(int, notify=camerasDetectedCountChanged)
    def camerasDetectedCount(self): return self._cameras_detected

    @pyqtProperty(str, notify=cameraDiscoveryHintChanged)
    def cameraDiscoveryHint(self): return self._camera_hint

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

    def push_frame(self, _provider=None):
        """Call after provider.update_frame(); increments the QML image URL counter."""
        self._frame_counter += 1
        self.frameCounterChanged.emit(self._frame_counter)

    def set_capturable(self, v: bool):
        v = bool(v)
        if self._capturable != v:
            self._capturable = v
            self.capturableChanged.emit(v)

    def set_brightness(self, v):
        v = max(0, min(100, v))
        if self._brightness != v:
            self._brightness = v; self.brightnessChanged.emit(v)

    def set_zoom(self, v):
        v = max(0, min(100, v))
        if self._zoom != v:
            self._zoom = v; self.zoomChanged.emit(v)

    def set_active_preset(self, idx):
        if self._active_preset != idx:
            self._active_preset = idx; self.activePresetChanged.emit(idx)

    def set_auto_color(self, v):
        if self._auto_color != v:
            self._auto_color = v; self.autoColorChanged.emit(v)

    def set_roi_mode(self, v):
        if self._roi_mode != v:
            self._roi_mode = v; self.roiModeChanged.emit(v)

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
        self.toast("Image captured")

    @pyqtSlot(bool)
    def onImageSettingsToggled(self, v):
        self._img_settings_vis = v
        self.imageSettingsVisibleChanged.emit(v)
        if v and self._settings_panel_vis:
            self._settings_panel_vis = False
            self.settingsPanelVisibleChanged.emit(False)

    @pyqtSlot(bool)
    def onSettingsPanelToggled(self, v):
        self._settings_panel_vis = v
        self.settingsPanelVisibleChanged.emit(v)
        if v and self._img_settings_vis:
            self._img_settings_vis = False
            self.imageSettingsVisibleChanged.emit(False)

    @pyqtSlot(int)
    def onBrightnessChanged(self, v): self.set_brightness(v)

    @pyqtSlot(int)
    def onZoomChanged(self, v): self.set_zoom(v)

    @pyqtSlot(int)
    def onPresetClicked(self, idx):
        self.set_active_preset(idx if self._active_preset != idx else -1)

    @pyqtSlot(int)
    def onPresetSave(self, idx): self.toast(f"Preset {idx + 1} saved")

    @pyqtSlot(bool)
    def onAutoColorToggled(self, v):
        self.set_auto_color(v)
        self.toast("Auto colour ON" if v else "Auto colour OFF")

    @pyqtSlot(bool)
    def onRoiModeToggled(self, v): self.set_roi_mode(v)

    @pyqtSlot()
    def onRecenterRoi(self): self.toast("ROI recentered")

    @pyqtSlot()
    def onFlipH(self): self.toast("Flipped horizontally")

    @pyqtSlot()
    def onFlipV(self): self.toast("Flipped vertically")

    @pyqtSlot()
    def onRotateCw(self): self.toast("Rotated 90° clockwise")

    @pyqtSlot()
    def onRotateCcw(self): self.toast("Rotated 90° counter-clockwise")

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
        for attr in ("_exposure","_gain","_white_balance","_contrast",
                     "_saturation","_warmth","_tint"):
            setattr(self, attr, 50)
        for sig in (self.exposureChanged, self.gainChanged, self.whiteBalanceChanged,
                    self.contrastChanged, self.saturationChanged,
                    self.warmthChanged, self.tintChanged):
            sig.emit(50)
        self.toast("Settings reset to defaults")

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
        if self._capture_format_png != png:
            self._capture_format_png = png
            self.captureFormatPngChanged.emit(png)

    @pyqtSlot(bool)
    def onLedsPresetAuto(self, auto_on):
        if self._leds_auto != auto_on:
            self._leds_auto = auto_on
            self.ledsPresetAutoChanged.emit(auto_on)

    @pyqtSlot(bool)
    def onCaptureBurstMode(self, burst):
        if self._capture_burst != burst:
            self._capture_burst = burst
            self.captureBurstModeChanged.emit(burst)

    @pyqtSlot(int)
    def onCaptureDelaySec(self, sec):
        if self._capture_delay_sec != sec:
            self._capture_delay_sec = sec
            self.captureDelaySecChanged.emit(sec)

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

    @pyqtSlot()
    def onExportAllClicked(self):
        self.toast("Export all (stub)")
