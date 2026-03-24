"""
Kiosk-style UI shell: full-screen live view with top status bar, right tool rail,
and bottom control bar (Occuscope-style layout).
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dental_imaging.ui.widgets.image_settings_component import ImageSettingsComponent
from dental_imaging.ui.widgets.preview_widget import PreviewWidget

# Semi-transparent dark chrome (reference: grey strips over live image)
CHROME_BG = "rgba(32, 34, 38, 0.88)"
CHROME_BORDER = "rgba(255, 255, 255, 0.08)"
LABEL_STYLE = "color: #f2f2f2; font-size: 12px;"
TITLE_STYLE = "color: #ffffff; font-weight: 600; font-size: 13px;"
MUTED_STYLE = "color: #b0b0b0; font-size: 10px;"


def _pill_button(text: str, checked: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setChecked(checked)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        """
        QPushButton {
            background-color: rgba(255,255,255,0.12);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 14px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 600;
        }
        QPushButton:checked {
            background-color: rgba(120, 200, 120, 0.35);
            border-color: rgba(160, 220, 160, 0.5);
        }
        QPushButton:hover { background-color: rgba(255,255,255,0.18); }
        """
    )
    return b


class TopStatusBar(QFrame):
    """Brand (left), stream stats pill (center-right), power / connection (far right)."""

    power_clicked = pyqtSignal()

    def __init__(self, brand_title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopStatusBar")
        self.setFixedHeight(52)
        self.setStyleSheet(
            f"""
            QFrame#TopStatusBar {{
                background-color: {CHROME_BG};
                border-bottom: 1px solid {CHROME_BORDER};
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        brand = QLabel(brand_title.replace(" — ", "\n").upper() if " — " in brand_title else brand_title.upper())
        brand.setStyleSheet(TITLE_STYLE)
        brand.setWordWrap(True)
        f = QFont()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        brand.setFont(f)
        layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch(1)

        self._stats = QLabel("— × —     — fps     — MB/s")
        self._stats.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self._stats, 0, Qt.AlignmentFlag.AlignVCenter)

        self._connected = _pill_button("DISCONNECTED", checked=False)
        self._connected.setEnabled(False)
        layout.addWidget(self._connected)

        power_col = QVBoxLayout()
        power_col.setSpacing(2)
        hint = QLabel("Connect / disconnect camera")
        hint.setStyleSheet(MUTED_STYLE)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._power = QPushButton("Power")
        self._power.setToolTip("Disconnect or reconnect the camera")
        self._power.setCursor(Qt.CursorShape.PointingHandCursor)
        self._power.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #e8e8e8;
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.08); }
            """
        )
        self._power.clicked.connect(self.power_clicked.emit)
        power_col.addWidget(hint, 0, Qt.AlignmentFlag.AlignCenter)
        power_col.addWidget(self._power, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(power_col)

    def set_stats_text(self, width: int, height: int, fps: float, mbps: float) -> None:
        self._stats.setText(
            f"{width} × {height}     {fps:.0f} fps     {mbps:.1f} MB/s"
        )

    def set_connected(self, connected: bool) -> None:
        self._connected.setEnabled(True)
        self._connected.setChecked(connected)
        self._connected.setText("CONNECTED" if connected else "DISCONNECTED")

    def set_power_primary_text(self, text: str) -> None:
        self._power.setText(text)


class RightToolRail(QFrame):
    """Vertical tool column: icons + labels (reference layout)."""

    flip_vertical_clicked = pyqtSignal()
    flip_horizontal_clicked = pyqtSignal()
    rotate_ccw_clicked = pyqtSignal()
    rotate_cw_clicked = pyqtSignal()
    image_settings_clicked = pyqtSignal(bool)
    settings_toggled = pyqtSignal(bool)
    capture_clicked = pyqtSignal()
    auto_color_clicked = pyqtSignal()
    recenter_roi_clicked = pyqtSignal()
    roi_mode_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RightToolRail")
        self.setFixedWidth(208)
        self.setStyleSheet(
            f"""
            QFrame#RightToolRail {{
                background-color: {CHROME_BG};
                border-left: 1px solid {CHROME_BORDER};
            }}
            QToolButton {{
                background-color: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                color: #fff;
                font-size: 16px;
                padding: 6px;
                min-width: 36px;
                min-height: 32px;
            }}
            QToolButton:hover {{ background-color: rgba(255,255,255,0.14); }}
            QToolButton:checked {{ background-color: rgba(80, 140, 220, 0.35); }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 16, 12, 16)
        root.setSpacing(14)

        def row(icon: str, label: str, *buttons: QToolButton) -> None:
            h = QHBoxLayout()
            h.setSpacing(8)
            for b in buttons:
                h.addWidget(b, 0, Qt.AlignmentFlag.AlignCenter)
            lab = QLabel(label)
            lab.setStyleSheet(LABEL_STYLE)
            lab.setWordWrap(True)
            h.addWidget(lab, 1)
            root.addLayout(h)

        b_fv = QToolButton()
        b_fv.setText("↕")
        b_fv.setToolTip("Flip vertical")
        b_fv.clicked.connect(self.flip_vertical_clicked.emit)
        b_fh = QToolButton()
        b_fh.setText("↔")
        b_fh.setToolTip("Flip horizontal")
        b_fh.clicked.connect(self.flip_horizontal_clicked.emit)
        row("", "Flip image", b_fv, b_fh)

        b_rc = QToolButton()
        b_rc.setText("↺")
        b_rc.setToolTip("Rotate counter-clockwise")
        b_rc.clicked.connect(self.rotate_ccw_clicked.emit)
        b_r = QToolButton()
        b_r.setText("↻")
        b_r.setToolTip("Rotate clockwise")
        b_r.clicked.connect(self.rotate_cw_clicked.emit)
        row("", "Rotate image", b_rc, b_r)

        self._img_settings = QToolButton()
        self._img_settings.setText("◐")
        self._img_settings.setToolTip("Image settings (exposure, color, …)")
        self._img_settings.setCheckable(True)
        self._img_settings.setChecked(True)
        self._img_settings.toggled.connect(self.image_settings_clicked.emit)
        row("", "Image settings", self._img_settings)

        self._settings_btn = QToolButton()
        self._settings_btn.setText("⚙")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setCheckable(True)
        self._settings_btn.setChecked(False)
        self._settings_btn.toggled.connect(self.settings_toggled.emit)
        row("", "Settings", self._settings_btn)

        self._capture_btn = QToolButton()
        self._capture_btn.setText("📷")
        self._capture_btn.setToolTip("Capture full-resolution image")
        self._capture_btn.clicked.connect(self.capture_clicked.emit)
        row("", "Capture", self._capture_btn)

        b_ac = QToolButton()
        b_ac.setText("◎")
        b_ac.setToolTip("Auto color balance (coming soon)")
        b_ac.clicked.connect(self.auto_color_clicked.emit)
        row("", "Auto color balance", b_ac)

        b_roi0 = QToolButton()
        b_roi0.setText("⊕")
        b_roi0.setToolTip("Recenter ROI")
        b_roi0.clicked.connect(self.recenter_roi_clicked.emit)
        row("", "Recenter ROI", b_roi0)

        b_roi = QToolButton()
        b_roi.setText("▢")
        b_roi.setToolTip("ROI mode (1-finger box)")
        b_roi.clicked.connect(self.roi_mode_clicked.emit)
        row("", "ROI mode (1 finger box)", b_roi)

        root.addStretch(1)

    def image_settings_button(self) -> QToolButton:
        return self._img_settings

    def settings_tool_button(self) -> QToolButton:
        return self._settings_btn

    def set_capture_enabled(self, enabled: bool) -> None:
        self._capture_btn.setEnabled(enabled)


class BottomControlBar(QFrame):
    """Brightness and zoom sliders + preset chips."""

    brightness_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(int)
    preset_clicked = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomControlBar")
        self.setFixedHeight(118)
        self.setStyleSheet(
            f"""
            QFrame#BottomControlBar {{
                background-color: {CHROME_BG};
                border-top: 1px solid {CHROME_BORDER};
            }}
            QLabel {{ {LABEL_STYLE} }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: rgba(255,255,255,0.15);
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #fff;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QPushButton#presetChip {{
                background-color: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 22px;
                color: #fff;
                min-width: 44px;
                min-height: 44px;
                font-weight: 600;
            }}
            QPushButton#presetChip:hover {{ background-color: rgba(255,255,255,0.18); }}
            """
        )

        grid = QGridLayout(self)
        grid.setContentsMargins(20, 10, 20, 14)
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(6)

        def labeled_slider(
            title: str, left_caption: str, right_caption: str, default: int = 50
        ):
            t = QLabel(title)
            t.setStyleSheet("font-weight: 600; color: #fff; font-size: 12px;")
            pct = QLabel(f"{default}%")
            pct.setMinimumWidth(36)
            pct.setAlignment(Qt.AlignmentFlag.AlignRight)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(0, 100)
            sl.setValue(default)
            foot = QHBoxLayout()
            a = QLabel(left_caption)
            a.setStyleSheet(MUTED_STYLE)
            b = QLabel(right_caption)
            b.setStyleSheet(MUTED_STYLE)
            b.setAlignment(Qt.AlignmentFlag.AlignRight)
            foot.addWidget(a)
            foot.addStretch()
            foot.addWidget(b)
            return t, pct, sl, foot

        br_title, br_pct, br_sl, br_foot = labeled_slider(
            "Brightness", "OFF", "HIGH", 50
        )
        self._brightness_slider = br_sl
        br_sl.valueChanged.connect(lambda v: br_pct.setText(f"{v}%"))
        br_sl.valueChanged.connect(self.brightness_changed.emit)

        zm_title, zm_pct, zm_sl, zm_foot = labeled_slider(
            "Zoom", "Widest", "Tightest", 0
        )
        self._zoom_slider = zm_sl
        zm_sl.valueChanged.connect(lambda v: zm_pct.setText(f"{v}%"))
        zm_sl.valueChanged.connect(self.zoom_changed.emit)

        grid.addWidget(br_title, 0, 0)
        grid.addWidget(br_pct, 0, 1)
        grid.addWidget(zm_title, 0, 2)
        grid.addWidget(zm_pct, 0, 3)

        grid.addWidget(br_sl, 1, 0, 1, 2)
        grid.addWidget(zm_sl, 1, 2, 1, 2)

        wf = QWidget()
        wfl = QVBoxLayout(wf)
        wfl.setContentsMargins(0, 0, 0, 0)
        wfl.addLayout(br_foot)
        grid.addWidget(wf, 2, 0, 1, 2)
        zf = QWidget()
        zfl = QVBoxLayout(zf)
        zfl.setContentsMargins(0, 0, 0, 0)
        zfl.addLayout(zm_foot)
        grid.addWidget(zf, 2, 2, 1, 2)

        preset_box = QVBoxLayout()
        preset_lbl = QLabel("Presets")
        preset_lbl.setStyleSheet(MUTED_STYLE)
        preset_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        for i in range(3):
            p = QPushButton(str(i + 1))
            p.setObjectName("presetChip")
            p.setCursor(Qt.CursorShape.PointingHandCursor)
            idx = i
            p.clicked.connect(lambda checked=False, n=idx: self.preset_clicked.emit(n))
            preset_row.addWidget(p)
        preset_box.addWidget(preset_lbl)
        preset_box.addLayout(preset_row)
        grid.addLayout(preset_box, 0, 4, 3, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)

    def brightness_percent(self) -> int:
        return self._brightness_slider.value()

    def zoom_percent(self) -> int:
        return self._zoom_slider.value()


class ClinicalViewport(QWidget):
    """
    Full-bleed live preview with overlaid chrome: top bar, right rail, bottom bar,
    and optional floating Image Settings panel (positioned left of the rail).
    """

    def __init__(
        self,
        preview: PreviewWidget,
        image_settings: ImageSettingsComponent,
        brand_title: str,
        settings_panel: Optional[QWidget] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._preview = preview
        self._overlay = image_settings
        self._settings = settings_panel
        self._top = TopStatusBar(brand_title, self)
        self._right = RightToolRail(self)
        self._bottom = BottomControlBar(self)

        preview.setParent(self)
        image_settings.setParent(self)
        self._top.setParent(self)
        self._right.setParent(self)
        self._bottom.setParent(self)
        if self._settings is not None:
            self._settings.setParent(self)
            self._settings.hide()

        self._top.raise_()
        self._right.raise_()
        self._bottom.raise_()
        image_settings.raise_()
        if self._settings is not None:
            self._settings.raise_()

    def top_bar(self) -> TopStatusBar:
        return self._top

    def right_rail(self) -> RightToolRail:
        return self._right

    def bottom_bar(self) -> BottomControlBar:
        return self._bottom

    def preview_widget(self) -> PreviewWidget:
        return self._preview

    def settings_panel(self) -> Optional[QWidget]:
        return self._settings

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.layout_chrome()

    def layout_chrome(self) -> None:
        """Position preview, rails, and floating panels (safe to call when toggling visibility)."""
        w, h = self.width(), self.height()
        th = self._top.height()
        rw = self._right.width()
        bh = self._bottom.height()

        self._top.setGeometry(0, 0, w, th)
        self._preview.setGeometry(0, th, max(0, w - rw), max(0, h - th - bh))
        self._right.setGeometry(w - rw, th, rw, max(0, h - th - bh))
        self._bottom.setGeometry(0, h - bh, w, bh)

        preview_h = max(0, h - th - bh)
        margin = 10
        panel = self._overlay
        panel.adjustSize()
        pw = panel.width()
        ph = panel.height()
        x = w - rw - pw - margin
        y = th + margin
        if x < margin:
            x = margin
        if y + ph > h - bh - margin:
            y = max(th + margin, h - bh - ph - margin)
        panel.move(x, y)

        if self._settings is not None and self._settings.isVisible():
            margin_s = 12
            avail_h = max(200, preview_h - 2 * margin_s)
            if hasattr(self._settings, "set_responsive_metrics"):
                self._settings.set_responsive_metrics(w - rw - 2 * margin_s, preview_h)
            self._settings.setMaximumHeight(avail_h)
            self._settings.adjustSize()
            sw = self._settings.width()
            sh = min(self._settings.sizeHint().height(), avail_h)
            self._settings.resize(sw, sh)
            sx = max(margin_s, w - rw - sw - margin_s)
            sy = th + margin_s + max(0, (preview_h - sh) // 2)
            if sy + sh > h - bh - margin_s:
                sy = max(th + margin_s, h - bh - sh - margin_s)
            self._settings.move(sx, sy)
            self._settings.raise_()

        self._overlay.raise_()
        if self._settings is not None and self._settings.isVisible():
            self._settings.raise_()
        self._top.raise_()
        self._right.raise_()
        self._bottom.raise_()
