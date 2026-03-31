"""
DentalBridge — QObject exposed to QML via context property "bridge".

All state that the QML UI needs flows through this object:
  Python → QML  via pyqtProperty / signals
  QML → Python  via @pyqtSlot methods called from QML JavaScript
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot


class DentalBridge(QObject):
    # ── Camera / connection state ──────────────────────────────────────────
    connectedChanged    = pyqtSignal(bool,  arguments=["connected"])
    statsTextChanged    = pyqtSignal(str,   arguments=["text"])
    frameCounterChanged = pyqtSignal()
    capturableChanged   = pyqtSignal(bool,  arguments=["capturable"])
    powerTextChanged    = pyqtSignal(str,   arguments=["text"])

    # ── Panel visibility ───────────────────────────────────────────────────
    imageSettingsVisibleChanged = pyqtSignal(bool, arguments=["visible"])
    settingsPanelVisibleChanged = pyqtSignal(bool, arguments=["visible"])

    # ── Bottom-bar state ───────────────────────────────────────────────────
    brightnessChanged   = pyqtSignal(int,  arguments=["value"])
    zoomChanged         = pyqtSignal(int,  arguments=["value"])
    activePresetChanged = pyqtSignal(int,  arguments=["index"])

    # ── Toggle state ───────────────────────────────────────────────────────
    autoColorChanged    = pyqtSignal(bool, arguments=["enabled"])
    roiModeChanged      = pyqtSignal(bool, arguments=["active"])
    imgSettingsChecked  = pyqtSignal(bool, arguments=["checked"])

    # ── Image-settings slider values (0-100) ──────────────────────────────
    exposureChanged     = pyqtSignal(int,  arguments=["v"])
    gainChanged         = pyqtSignal(int,  arguments=["v"])
    whiteBalanceChanged = pyqtSignal(int,  arguments=["v"])
    contrastChanged     = pyqtSignal(int,  arguments=["v"])
    saturationChanged   = pyqtSignal(int,  arguments=["v"])
    warmthChanged       = pyqtSignal(int,  arguments=["v"])
    tintChanged         = pyqtSignal(int,  arguments=["v"])

    # ── Toast ──────────────────────────────────────────────────────────────
    toastRequested = pyqtSignal(str, arguments=["message"])

    # ── QML → Python: actions ─────────────────────────────────────────────
    powerClicked          = pyqtSignal()
    flipHClicked          = pyqtSignal()
    flipVClicked          = pyqtSignal()
    rotateCwClicked       = pyqtSignal()
    rotateCcwClicked      = pyqtSignal()
    captureClicked        = pyqtSignal()
    autoColorToggled      = pyqtSignal(bool)
    roiModeToggled        = pyqtSignal(bool)
    recenterRoiClicked    = pyqtSignal()
    imageSettingsToggled  = pyqtSignal(bool)
    settingsPanelToggled  = pyqtSignal(bool)
    brightnessUserChanged = pyqtSignal(int)
    zoomUserChanged       = pyqtSignal(int)
    presetClicked         = pyqtSignal(int)
    presetSaveRequested   = pyqtSignal(int)
    imageSettingsReset    = pyqtSignal()
    exposureUserChanged   = pyqtSignal(int)
    gainUserChanged       = pyqtSignal(int)
    whiteBalanceUserChanged = pyqtSignal(int)
    contrastUserChanged   = pyqtSignal(int)
    saturationUserChanged = pyqtSignal(int)
    warmthUserChanged     = pyqtSignal(int)
    tintUserChanged       = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._connected   = False
        self._stats_text  = "— X —     — fps     — MB/s"
        self._frame_cnt   = 0
        self._capturable  = False
        self._power_text  = "Connect"
        self._img_vis     = False
        self._set_vis     = False
        self._brightness  = 50
        self._zoom        = 0
        self._active_preset = -1
        self._auto_color  = False
        self._roi_mode    = False
        self._img_checked = True
        # image settings (0-100)
        self._exposure    = 50
        self._gain        = 50
        self._wb          = 50
        self._contrast    = 50
        self._saturation  = 50
        self._warmth      = 50
        self._tint        = 50

    # ── pyqtProperty declarations ──────────────────────────────────────────

    @pyqtProperty(bool, notify=connectedChanged)
    def connected(self): return self._connected

    @pyqtProperty(str, notify=statsTextChanged)
    def statsText(self): return self._stats_text

    @pyqtProperty(int, notify=frameCounterChanged)
    def frameCounter(self): return self._frame_cnt

    @pyqtProperty(bool, notify=capturableChanged)
    def capturable(self): return self._capturable

    @pyqtProperty(str, notify=powerTextChanged)
    def powerText(self): return self._power_text

    @pyqtProperty(bool, notify=imageSettingsVisibleChanged)
    def imageSettingsVisible(self): return self._img_vis

    @pyqtProperty(bool, notify=settingsPanelVisibleChanged)
    def settingsPanelVisible(self): return self._set_vis

    @pyqtProperty(int, notify=brightnessChanged)
    def brightness(self): return self._brightness

    @pyqtProperty(int, notify=zoomChanged)
    def zoom(self): return self._zoom

    @pyqtProperty(int, notify=activePresetChanged)
    def activePreset(self): return self._active_preset

    @pyqtProperty(bool, notify=autoColorChanged)
    def autoColor(self): return self._auto_color

    @pyqtProperty(bool, notify=roiModeChanged)
    def roiMode(self): return self._roi_mode

    @pyqtProperty(bool, notify=imgSettingsChecked)
    def imgSettingsCheckedState(self): return self._img_checked

    @pyqtProperty(int, notify=exposureChanged)
    def exposure(self): return self._exposure

    @pyqtProperty(int, notify=gainChanged)
    def gain(self): return self._gain

    @pyqtProperty(int, notify=whiteBalanceChanged)
    def whiteBalance(self): return self._wb

    @pyqtProperty(int, notify=contrastChanged)
    def contrast(self): return self._contrast

    @pyqtProperty(int, notify=saturationChanged)
    def saturation(self): return self._saturation

    @pyqtProperty(int, notify=warmthChanged)
    def warmth(self): return self._warmth

    @pyqtProperty(int, notify=tintChanged)
    def tint(self): return self._tint

    # ── Python → QML setters ──────────────────────────────────────────────

    def set_connected(self, v: bool) -> None:
        if self._connected != v:
            self._connected = v
            self.connectedChanged.emit(v)

    def set_stats(self, w: int, h: int, fps: float, mbps: float) -> None:
        t = f"{w} X {h}     {fps:.0f} fps     {mbps:.1f} MB/s"
        if t != self._stats_text:
            self._stats_text = t
            self.statsTextChanged.emit(t)

    def increment_frame(self) -> None:
        self._frame_cnt += 1
        self.frameCounterChanged.emit()

    def set_capturable(self, v: bool) -> None:
        if self._capturable != v:
            self._capturable = v
            self.capturableChanged.emit(v)

    def set_power_text(self, t: str) -> None:
        if t != self._power_text:
            self._power_text = t
            self.powerTextChanged.emit(t)

    def set_brightness(self, v: int) -> None:
        if self._brightness != v:
            self._brightness = v
            self.brightnessChanged.emit(v)

    def set_zoom(self, v: int) -> None:
        if self._zoom != v:
            self._zoom = v
            self.zoomChanged.emit(v)

    def set_active_preset(self, idx: int) -> None:
        if self._active_preset != idx:
            self._active_preset = idx
            self.activePresetChanged.emit(idx)

    def set_auto_color(self, v: bool) -> None:
        if self._auto_color != v:
            self._auto_color = v
            self.autoColorChanged.emit(v)

    def set_roi_mode(self, v: bool) -> None:
        if self._roi_mode != v:
            self._roi_mode = v
            self.roiModeChanged.emit(v)

    def set_img_settings_visible(self, v: bool) -> None:
        if self._img_vis != v:
            self._img_vis = v
            self.imageSettingsVisibleChanged.emit(v)

    def set_settings_panel_visible(self, v: bool) -> None:
        if self._set_vis != v:
            self._set_vis = v
            self.settingsPanelVisibleChanged.emit(v)

    def set_img_settings_checked(self, v: bool) -> None:
        if self._img_checked != v:
            self._img_checked = v
            self.imgSettingsChecked.emit(v)

    def show_toast(self, msg: str) -> None:
        self.toastRequested.emit(msg)

    def update_image_settings(
        self, exposure: int, gain: int, wb: int,
        contrast: int, saturation: int, warmth: int, tint: int,
    ) -> None:
        self._exposure = exposure; self.exposureChanged.emit(exposure)
        self._gain = gain;         self.gainChanged.emit(gain)
        self._wb = wb;             self.whiteBalanceChanged.emit(wb)
        self._contrast = contrast; self.contrastChanged.emit(contrast)
        self._saturation = saturation; self.saturationChanged.emit(saturation)
        self._warmth = warmth;     self.warmthChanged.emit(warmth)
        self._tint = tint;         self.tintChanged.emit(tint)

    # ── @pyqtSlot — called directly from QML JavaScript ───────────────────

    @pyqtSlot()
    def onPowerClicked(self): self.powerClicked.emit()

    @pyqtSlot()
    def onFlipH(self): self.flipHClicked.emit()

    @pyqtSlot()
    def onFlipV(self): self.flipVClicked.emit()

    @pyqtSlot()
    def onRotateCw(self): self.rotateCwClicked.emit()

    @pyqtSlot()
    def onRotateCcw(self): self.rotateCcwClicked.emit()

    @pyqtSlot()
    def onCapture(self): self.captureClicked.emit()

    @pyqtSlot(bool)
    def onAutoColorToggled(self, v: bool):
        self._auto_color = v
        self.autoColorToggled.emit(v)

    @pyqtSlot(bool)
    def onRoiModeToggled(self, v: bool):
        self._roi_mode = v
        self.roiModeToggled.emit(v)

    @pyqtSlot()
    def onRecenterRoi(self): self.recenterRoiClicked.emit()

    @pyqtSlot(bool)
    def onImageSettingsToggled(self, v: bool):
        self._img_vis = v
        self._img_checked = v
        self.imageSettingsVisibleChanged.emit(v)
        self.imageSettingsToggled.emit(v)

    @pyqtSlot(bool)
    def onSettingsPanelToggled(self, v: bool):
        self._set_vis = v
        if v:
            self._img_vis = False
            self.imageSettingsVisibleChanged.emit(False)
        self.settingsPanelVisibleChanged.emit(v)
        self.settingsPanelToggled.emit(v)

    @pyqtSlot(int)
    def onBrightnessChanged(self, v: int):
        self._brightness = v
        self.brightnessUserChanged.emit(v)

    @pyqtSlot(int)
    def onZoomChanged(self, v: int):
        self._zoom = v
        self.zoomUserChanged.emit(v)

    @pyqtSlot(int)
    def onPresetClicked(self, idx: int):
        self._active_preset = idx
        self.presetClicked.emit(idx)

    @pyqtSlot(int)
    def onPresetSave(self, idx: int):
        self.presetSaveRequested.emit(idx)

    @pyqtSlot()
    def onImageSettingsReset(self): self.imageSettingsReset.emit()

    @pyqtSlot(int)
    def onExposureChanged(self, v: int):
        self._exposure = v; self.exposureUserChanged.emit(v)

    @pyqtSlot(int)
    def onGainChanged(self, v: int):
        self._gain = v; self.gainUserChanged.emit(v)

    @pyqtSlot(int)
    def onWhiteBalanceChanged(self, v: int):
        self._wb = v; self.whiteBalanceUserChanged.emit(v)

    @pyqtSlot(int)
    def onContrastChanged(self, v: int):
        self._contrast = v; self.contrastUserChanged.emit(v)

    @pyqtSlot(int)
    def onSaturationChanged(self, v: int):
        self._saturation = v; self.saturationUserChanged.emit(v)

    @pyqtSlot(int)
    def onWarmthChanged(self, v: int):
        self._warmth = v; self.warmthUserChanged.emit(v)

    @pyqtSlot(int)
    def onTintChanged(self, v: int):
        self._tint = v; self.tintUserChanged.emit(v)
