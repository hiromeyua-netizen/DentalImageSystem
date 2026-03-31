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
    burstActiveChanged          = pyqtSignal(bool)
    burstProgressTextChanged    = pyqtSignal(str)
    captureDelaySecChanged      = pyqtSignal(int)
    cameraSoundEnabledChanged   = pyqtSignal(bool)
    storageSdcardChanged        = pyqtSignal(bool)
    camerasDetectedCountChanged = pyqtSignal(int)
    cameraDiscoveryHintChanged  = pyqtSignal(str)
    ledControllerConnectedChanged = pyqtSignal(bool)
    ledControllerPortChanged    = pyqtSignal(str)
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
        self._capture_burst      = True
        self._burst_active       = False
        self._burst_progress     = ""
        self._capture_delay_sec  = 10
        self._camera_sound       = False
        self._storage_sdcard     = False
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
