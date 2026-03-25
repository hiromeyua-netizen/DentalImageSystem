"""
QmlClinicalViewport
───────────────────
Drop-in replacement for ClinicalViewport (clinical_shell.py) that renders the
chrome via QML.  The public API (top_bar(), right_rail(), bottom_bar(),
layout_chrome()) is preserved so MainWindow needs only minimal changes.

Camera frames are served to QML through CameraFrameProvider.
Python ↔ QML communication flows through DentalBridge.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtQuickWidgets import QQuickWidget
from PyQt6.QtWidgets import QWidget

from dental_imaging.ui.bridge import DentalBridge
from dental_imaging.ui.camera_provider import CameraFrameProvider

_QML_DIR = Path(__file__).parent / "qml"


# ---------------------------------------------------------------------------
# Proxy objects — expose the same signal/slot surface as the old shell widgets
# ---------------------------------------------------------------------------

class _TopBarProxy(QObject):
    """Proxy for TopStatusBar — delegates to DentalBridge."""
    power_clicked = pyqtSignal()

    def __init__(self, bridge: DentalBridge, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        bridge.powerClicked.connect(self.power_clicked)
        self._b = bridge

    def set_connected(self, connected: bool) -> None:
        self._b.set_connected(connected)

    def set_power_primary_text(self, text: str) -> None:
        self._b.set_power_text(text)

    def set_stats_text(self, w: int, h: int, fps: float, mbps: float) -> None:
        self._b.set_stats(w, h, fps, mbps)


class _ImageSettingsButtonProxy(QObject):
    """
    Proxy for the QToolButton returned by rail.image_settings_button().
    Needed so ImageSettingsComponent.wire_toggle_button() still works.
    """
    toggled = pyqtSignal(bool)

    def __init__(self, bridge: DentalBridge, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._b = bridge
        bridge.imageSettingsToggled.connect(self.toggled)

    def setChecked(self, checked: bool) -> None:
        self._b.set_img_settings_checked(checked)

    def isChecked(self) -> bool:
        return self._b.imgSettingsCheckedState


class _RailProxy(QObject):
    """Proxy for RightToolRail — forwards bridge signals outward."""
    capture_clicked        = pyqtSignal()
    settings_toggled       = pyqtSignal(bool)
    flip_horizontal_clicked = pyqtSignal()
    flip_vertical_clicked  = pyqtSignal()
    rotate_ccw_clicked     = pyqtSignal()
    rotate_cw_clicked      = pyqtSignal()
    auto_color_toggled     = pyqtSignal(bool)
    recenter_roi_clicked   = pyqtSignal()
    roi_mode_toggled       = pyqtSignal(bool)
    image_settings_clicked = pyqtSignal(bool)

    def __init__(self, bridge: DentalBridge, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._b = bridge
        self._img_btn = _ImageSettingsButtonProxy(bridge, parent=self)

        bridge.captureClicked.connect(self.capture_clicked)
        bridge.settingsPanelToggled.connect(self.settings_toggled)
        bridge.flipHClicked.connect(self.flip_horizontal_clicked)
        bridge.flipVClicked.connect(self.flip_vertical_clicked)
        bridge.rotateCcwClicked.connect(self.rotate_ccw_clicked)
        bridge.rotateCwClicked.connect(self.rotate_cw_clicked)
        bridge.autoColorToggled.connect(self.auto_color_toggled)
        bridge.recenterRoiClicked.connect(self.recenter_roi_clicked)
        bridge.roiModeToggled.connect(self.roi_mode_toggled)
        bridge.imageSettingsToggled.connect(self.image_settings_clicked)

    def image_settings_button(self) -> _ImageSettingsButtonProxy:
        return self._img_btn

    def settings_tool_button(self) -> _ImageSettingsButtonProxy:
        return self._img_btn      # not used directly in MainWindow

    def auto_color_button(self) -> None:
        return None               # MainWindow only uses .setChecked

    def roi_mode_button(self) -> None:
        return None

    def set_capture_enabled(self, enabled: bool) -> None:
        self._b.set_capturable(enabled)

    def set_auto_color_checked(self, v: bool) -> None:
        self._b.set_auto_color(v)

    def set_roi_mode_checked(self, v: bool) -> None:
        self._b.set_roi_mode(v)


class _BottomProxy(QObject):
    """Proxy for BottomControlBar — delegates to DentalBridge."""
    brightness_changed    = pyqtSignal(int)
    zoom_changed          = pyqtSignal(int)
    preset_clicked        = pyqtSignal(int)
    preset_save_requested = pyqtSignal(int)

    def __init__(self, bridge: DentalBridge, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._b = bridge
        bridge.brightnessUserChanged.connect(self.brightness_changed)
        bridge.zoomUserChanged.connect(self.zoom_changed)
        bridge.presetClicked.connect(self.preset_clicked)
        bridge.presetSaveRequested.connect(self.preset_save_requested)

    def brightness_percent(self) -> int:
        return self._b.brightness

    def zoom_percent(self) -> int:
        return self._b.zoom

    def set_brightness_percent(self, v: int) -> None:
        self._b.set_brightness(max(0, min(100, int(v))))

    def set_zoom_percent(self, v: int) -> None:
        self._b.set_zoom(max(0, min(100, int(v))))

    def set_active_preset(self, idx: int) -> None:
        self._b.set_active_preset(idx)


# ---------------------------------------------------------------------------
# Main viewport widget
# ---------------------------------------------------------------------------

class QmlClinicalViewport(QWidget):
    """
    Full-bleed QML viewport.  Replace ClinicalViewport(…) with this class;
    the rest of MainWindow stays identical.
    """

    def __init__(
        self,
        app_name: str = "DENTAL IMAGING",
        app_sub_name: str = "SYSTEM",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self._bridge   = DentalBridge(self)
        self._provider = CameraFrameProvider()

        # ── QQuickWidget ───────────────────────────────────────────────────
        self._qml = QQuickWidget(self)
        self._qml.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self._qml.setAttribute(  # transparent background so camera shows through
            __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.WidgetAttribute.WA_TranslucentBackground
        )

        engine = self._qml.engine()
        engine.addImageProvider("camera", self._provider)
        ctx = engine.rootContext()
        ctx.setContextProperty("bridge",     self._bridge)
        ctx.setContextProperty("appName",    app_name)
        ctx.setContextProperty("appSubName", app_sub_name)

        qml_main = _QML_DIR / "main.qml"
        self._qml.setSource(QUrl.fromLocalFile(str(qml_main)))

        # Stretch qml to fill
        self._qml.move(0, 0)
        self._qml.resize(self.size())

        # ── Proxy objects (same API as old shell widgets) ──────────────────
        self._top_proxy    = _TopBarProxy(self._bridge, parent=self)
        self._rail_proxy   = _RailProxy(self._bridge, parent=self)
        self._bottom_proxy = _BottomProxy(self._bridge, parent=self)

    # ── Public API matching ClinicalViewport ───────────────────────────────

    def top_bar(self)    -> _TopBarProxy:    return self._top_proxy
    def right_rail(self) -> _RailProxy:      return self._rail_proxy
    def bottom_bar(self) -> _BottomProxy:    return self._bottom_proxy

    def layout_chrome(self) -> None:
        """No-op: QML handles layout natively via anchors."""
        pass

    def settings_panel(self):
        return None  # settings live in QML

    # ── Frame delivery ─────────────────────────────────────────────────────

    def push_frame(self, bgr_frame) -> None:
        """Called from MainWindow.update_preview() with the processed BGR array."""
        self._provider.update_frame(bgr_frame)
        self._bridge.increment_frame()

    # ── Bridge accessor (for MainWindow to wire toasts etc.) ───────────────

    def bridge(self) -> DentalBridge:
        return self._bridge

    # ── Resize ────────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._qml.resize(self.size())
