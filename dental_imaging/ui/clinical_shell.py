"""
Kiosk-style UI shell: full-screen live view with top status bar, right tool rail,
and bottom control bar (Occuscope-style layout).
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
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

# Semi-transparent dark chrome (~50–55% opacity over live image, reference Occuscope)
CHROME_BG = "rgba(28, 30, 34, 0.55)"
CHROME_BORDER = "rgba(255, 255, 255, 0.10)"
CHROME_RADIUS_PX = 14
LABEL_STYLE = "color: #f2f2f2; font-size: 12px;"
TITLE_STYLE = "color: #ffffff; font-weight: 600; font-size: 13px;"
MUTED_STYLE = "color: #b0b0b0; font-size: 10px;"


def _clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


class ClinicalValueSlider(QSlider):
    """Horizontal slider with the value drawn inside the circular thumb (reference UI)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._handle_r = 14
        self._groove_h = 6
        self._h_margin = 6

    def set_visual_metrics(self, handle_r: int, groove_h: int, h_margin: int) -> None:
        self._handle_r = max(10, handle_r)
        self._groove_h = max(4, groove_h)
        self._h_margin = max(4, h_margin)
        self.setMinimumHeight(self._handle_r * 2 + 6)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        hr = self._handle_r
        gh = self._groove_h
        mx = self._h_margin
        gw = max(1, w - 2 * mx)
        gx = mx
        gy = (h - gh) // 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 42)))
        painter.drawRoundedRect(gx, gy, gw, gh, gh // 2, gh // 2)

        span = self.maximum() - self.minimum()
        frac = (
            (self.value() - self.minimum()) / span
            if span > 0
            else 0.0
        )
        cx = int(round(gx + hr + frac * max(0.0, gw - 2 * hr)))
        cy = h // 2
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0, 55), 1))
        painter.drawEllipse(QPointF(cx, cy), float(hr), float(hr))

        painter.setPen(QPen(QColor(35, 35, 38)))
        f = self.font()
        f.setPixelSize(_clamp_int(hr - 4, 8, 13))
        f.setWeight(QFont.Weight.DemiBold)
        painter.setFont(f)
        painter.drawText(
            QRectF(cx - hr, cy - hr, 2 * hr, 2 * hr),
            int(Qt.AlignmentFlag.AlignCenter),
            f"{self.value()}%",
        )

    def minimumSizeHint(self):
        return QSize(self._handle_r * 4, self._handle_r * 2 + 8)


class TopStatusBar(QFrame):
    """Brand (left), stream stats pill (center-right), power / connection (far right)."""

    power_clicked = pyqtSignal()

    def __init__(self, brand_title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopStatusBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"""
            QFrame#TopStatusBar {{
                background-color: {CHROME_BG};
                border: 1px solid {CHROME_BORDER};
                border-radius: {CHROME_RADIUS_PX}px;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        self._brand = QLabel(
            brand_title.replace(" — ", "\n").upper()
            if " — " in brand_title
            else brand_title.upper()
        )
        self._brand.setStyleSheet(TITLE_STYLE)
        self._brand.setWordWrap(True)
        f = QFont()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        self._brand.setFont(f)
        layout.addWidget(
            self._brand, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addStretch(1)

        self._stats_pill = QFrame()
        self._stats_pill.setObjectName("TopStatsPill")
        self._stats_pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        spl = QHBoxLayout(self._stats_pill)
        spl.setContentsMargins(14, 6, 14, 6)
        self._stats = QLabel("— X —     — fps     — MB/s")
        self._stats.setStyleSheet(LABEL_STYLE)
        spl.addWidget(self._stats)
        layout.addWidget(self._stats_pill, 0, Qt.AlignmentFlag.AlignVCenter)

        self._connected = QPushButton("DISCONNECTED")
        self._connected.setCheckable(True)
        self._connected.setChecked(False)
        self._connected.setEnabled(False)
        self._connected.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._connected)

        self._power = QPushButton("\u23FB")
        self._power.setObjectName("TopPowerButton")
        self._power.setToolTip("Connect")
        self._power.setCursor(Qt.CursorShape.PointingHandCursor)
        self._power.setFixedSize(44, 44)
        self._power.clicked.connect(self.power_clicked.emit)
        layout.addWidget(self._power, 0, Qt.AlignmentFlag.AlignVCenter)

        self.sync_touch_metrics(1080)

    def set_stats_text(self, width: int, height: int, fps: float, mbps: float) -> None:
        self._stats.setText(
            f"{width} X {height}     {fps:.0f} fps     {mbps:.1f} MB/s"
        )

    def sync_touch_metrics(self, short_edge: int) -> None:
        """Scale top bar for display size / touch (called from viewport resize)."""
        h = _clamp_int(short_edge // 19, 52, 64)
        self.setFixedHeight(h)
        stat_pt = _clamp_int(short_edge // 90, 11, 14)
        title_pt = _clamp_int(short_edge // 85, 12, 16)
        self._stats.setStyleSheet(
            f"color: #f2f2f2; font-size: {stat_pt}px; font-weight: 500; letter-spacing: 0.35px;"
        )
        self._brand.setStyleSheet(
            f"color: #ffffff; font-weight: 600; font-size: {title_pt}px;"
        )
        pill_pt = _clamp_int(short_edge // 95, 10, 12)
        pr = _clamp_int(short_edge // 55, 14, 22)
        self._stats_pill.setStyleSheet(
            f"""
            QFrame#TopStatsPill {{
                background-color: rgba(0, 0, 0, 0.32);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: {pr}px;
            }}
            """
        )
        self._connected.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.14);
                color: #f0f0f0;
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: {pr}px;
                padding: 6px 16px;
                font-size: {pill_pt}px;
                font-weight: 700;
                min-height: 28px;
            }}
            QPushButton:checked {{
                background-color: #ffffff;
                color: #1e1e22;
                border: 1px solid #ffffff;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.22);
            }}
            QPushButton:checked:hover {{
                background-color: #f5f5f7;
                color: #121216;
            }}
            """
        )
        pw = _clamp_int(short_edge // 24, 40, 52)
        power_pt = _clamp_int(short_edge // 50, 18, 26)
        self._power.setFixedSize(pw, pw)
        self._power.setStyleSheet(
            f"""
            QPushButton#TopPowerButton {{
                background-color: rgba(255, 255, 255, 0.95);
                color: #1a1a1f;
                border: none;
                border-radius: {pw // 2}px;
                font-size: {power_pt}px;
                font-weight: 700;
            }}
            QPushButton#TopPowerButton:hover {{
                background-color: #ffffff;
            }}
            QPushButton#TopPowerButton:pressed {{
                background-color: #e8e8ec;
            }}
            """
        )

    def set_connected(self, connected: bool) -> None:
        self._connected.setEnabled(True)
        self._connected.setChecked(connected)
        self._connected.setText("CONNECTED" if connected else "DISCONNECTED")

    def set_power_primary_text(self, text: str) -> None:
        self._power.setToolTip(text)


class RightToolRail(QFrame):
    """Vertical tool column: icons + labels (reference layout)."""

    flip_vertical_clicked = pyqtSignal()
    flip_horizontal_clicked = pyqtSignal()
    rotate_ccw_clicked = pyqtSignal()
    rotate_cw_clicked = pyqtSignal()
    image_settings_clicked = pyqtSignal(bool)
    settings_toggled = pyqtSignal(bool)
    capture_clicked = pyqtSignal()
    auto_color_toggled = pyqtSignal(bool)
    recenter_roi_clicked = pyqtSignal()
    roi_mode_toggled = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RightToolRail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._rail_labels: list[QLabel] = []
        self._root_layout: Optional[QVBoxLayout] = None

        root = QVBoxLayout(self)
        self._root_layout = root
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
            self._rail_labels.append(lab)
            h.addWidget(lab, 1)
            root.addLayout(h)

        # Order matches reference: horizontal flip, vertical flip, CW, CCW, gallery, …
        b_fh = QToolButton()
        b_fh.setText("\u2194")
        b_fh.setToolTip("Flip horizontal")
        b_fh.clicked.connect(self.flip_horizontal_clicked.emit)
        b_fv = QToolButton()
        b_fv.setText("\u2195")
        b_fv.setToolTip("Flip vertical")
        b_fv.clicked.connect(self.flip_vertical_clicked.emit)
        row("", "Flip", b_fh, b_fv)

        b_r = QToolButton()
        b_r.setText("\u21bb")
        b_r.setToolTip("Rotate clockwise")
        b_r.clicked.connect(self.rotate_cw_clicked.emit)
        b_rc = QToolButton()
        b_rc.setText("\u21ba")
        b_rc.setToolTip("Rotate counter-clockwise")
        b_rc.clicked.connect(self.rotate_ccw_clicked.emit)
        row("", "Rotate", b_r, b_rc)

        self._img_settings = QToolButton()
        self._img_settings.setText("\u25A3")
        self._img_settings.setToolTip("Image settings (exposure, color, …)")
        self._img_settings.setCheckable(True)
        self._img_settings.setChecked(True)
        self._img_settings.toggled.connect(self.image_settings_clicked.emit)
        row("", "Image / gallery", self._img_settings)

        self._settings_btn = QToolButton()
        self._settings_btn.setText("\u2699")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setCheckable(True)
        self._settings_btn.setChecked(False)
        self._settings_btn.toggled.connect(self.settings_toggled.emit)
        row("", "Settings", self._settings_btn)

        self._capture_btn = QToolButton()
        self._capture_btn.setText("\U0001f4f7")
        self._capture_btn.setToolTip("Capture full-resolution image")
        self._capture_btn.clicked.connect(self.capture_clicked.emit)
        row("", "Capture", self._capture_btn)

        self._auto_color_btn = QToolButton()
        self._auto_color_btn.setObjectName("autoColorBtn")
        self._auto_color_btn.setText("\u25CE")
        self._auto_color_btn.setToolTip("Auto color balance")
        self._auto_color_btn.setCheckable(True)
        self._auto_color_btn.setChecked(False)
        self._auto_color_btn.toggled.connect(self.auto_color_toggled.emit)
        row("", "Color balance", self._auto_color_btn)

        b_roi0 = QToolButton()
        b_roi0.setText("\u2316")
        b_roi0.setToolTip("Recenter ROI")
        b_roi0.clicked.connect(self.recenter_roi_clicked.emit)
        row("", "Recenter ROI", b_roi0)

        self._roi_mode_btn = QToolButton()
        self._roi_mode_btn.setObjectName("roiModeBtn")
        self._roi_mode_btn.setText("\u229E")
        self._roi_mode_btn.setToolTip("ROI mode (draw region)")
        self._roi_mode_btn.setCheckable(True)
        self._roi_mode_btn.setChecked(False)
        self._roi_mode_btn.toggled.connect(self.roi_mode_toggled.emit)
        row("", "ROI", self._roi_mode_btn)

        root.addStretch(1)

        self.sync_touch_metrics(1080)

    def image_settings_button(self) -> QToolButton:
        return self._img_settings

    def settings_tool_button(self) -> QToolButton:
        return self._settings_btn

    def auto_color_button(self) -> QToolButton:
        return self._auto_color_btn

    def roi_mode_button(self) -> QToolButton:
        return self._roi_mode_btn

    def set_capture_enabled(self, enabled: bool) -> None:
        self._capture_btn.setEnabled(enabled)

    def sync_touch_metrics(self, short_edge: int) -> None:
        rw = _clamp_int(short_edge // 5, 200, 244)
        self.setFixedWidth(rw)
        btn_min = _clamp_int(short_edge // 22, 46, 58)
        pad = _clamp_int(short_edge // 135, 6, 10)
        radius = _clamp_int(short_edge // 180, 6, 10)
        icon_pt = _clamp_int(short_edge // 68, 15, 20)
        lbl_pt = _clamp_int(short_edge // 78, 11, 14)
        rr = _clamp_int(short_edge // 55, 10, 18)
        self.setStyleSheet(
            f"""
            QFrame#RightToolRail {{
                background-color: {CHROME_BG};
                border: 1px solid {CHROME_BORDER};
                border-radius: {rr}px;
            }}
            QToolButton {{
                background-color: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: {radius}px;
                color: #fff;
                font-size: {icon_pt}px;
                padding: {pad}px;
                min-width: {btn_min}px;
                min-height: {btn_min}px;
            }}
            QToolButton:hover {{ background-color: rgba(255,255,255,0.16); }}
            QToolButton:pressed {{ background-color: rgba(255,255,255,0.22); }}
            QToolButton:checked {{ background-color: rgba(80, 140, 220, 0.38);
                border-color: rgba(140, 180, 240, 0.45); }}
            QToolButton#autoColorBtn:checked, QToolButton#roiModeBtn:checked {{
                background-color: rgba(90, 170, 110, 0.48);
                border-color: rgba(140, 220, 160, 0.55);
            }}
            """
        )
        for lab in self._rail_labels:
            lab.setStyleSheet(
                f"color: #f2f2f2; font-size: {lbl_pt}px; font-weight: 500;"
            )
        if self._root_layout is not None:
            mx = _clamp_int(short_edge // 110, 8, 14)
            my = _clamp_int(short_edge // 68, 12, 20)
            self._root_layout.setContentsMargins(mx, my, mx, my)
            self._root_layout.setSpacing(_clamp_int(short_edge // 77, 10, 16))


class BottomControlBar(QFrame):
    """Brightness and zoom sliders + preset chips."""

    brightness_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(int)
    preset_clicked = pyqtSignal(int)
    preset_save_requested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomControlBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._grid = QGridLayout(self)
        grid = self._grid
        grid.setContentsMargins(20, 10, 20, 14)
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(6)

        def labeled_slider(
            title: str, left_caption: str, right_caption: str, default: int = 50
        ):
            t = QLabel(title)
            t.setStyleSheet("font-weight: 600; color: #fff; font-size: 12px;")
            sl = ClinicalValueSlider()
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
            return t, sl, foot

        self._br_title, br_sl, br_foot = labeled_slider(
            "Brightness", "OFF", "HIGH", 50
        )
        self._brightness_slider = br_sl
        br_sl.valueChanged.connect(self.brightness_changed.emit)

        self._zm_title, zm_sl, zm_foot = labeled_slider(
            "Zoom", "Widest", "Tightest", 0
        )
        self._zoom_slider = zm_sl
        zm_sl.valueChanged.connect(self.zoom_changed.emit)

        grid.addWidget(self._br_title, 0, 0, 1, 2)
        grid.addWidget(self._zm_title, 0, 2, 1, 2)

        def slider_row(
            left_glyph: str,
            slider: ClinicalValueSlider,
            right_glyph: str | None,
            *,
            right_large: bool = False,
        ) -> QWidget:
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(10)
            left_lbl = QLabel(left_glyph)
            left_lbl.setObjectName("BottomBarGlyph")
            left_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_lbl.setFixedWidth(36)
            hl.addWidget(left_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            hl.addWidget(slider, 1)
            if right_glyph is not None:
                right_lbl = QLabel(right_glyph)
                right_lbl.setObjectName(
                    "BottomBarGlyphLarge" if right_large else "BottomBarGlyph"
                )
                right_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                right_lbl.setFixedWidth(44 if right_large else 36)
                hl.addWidget(right_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            return row

        br_row = slider_row("\u2600", br_sl, "\u2600", right_large=True)
        zm_out = "\U0001f50d\u2212"
        zm_in = "\U0001f50d+"
        zm_row = slider_row(zm_out, zm_sl, zm_in)
        grid.addWidget(br_row, 1, 0, 1, 2)
        grid.addWidget(zm_row, 1, 2, 1, 2)

        self._br_footer_wrap = QWidget()
        wfl = QVBoxLayout(self._br_footer_wrap)
        wfl.setContentsMargins(0, 0, 0, 0)
        wfl.addLayout(br_foot)
        grid.addWidget(self._br_footer_wrap, 2, 0, 1, 2)
        self._zm_footer_wrap = QWidget()
        zfl = QVBoxLayout(self._zm_footer_wrap)
        zfl.setContentsMargins(0, 0, 0, 0)
        zfl.addLayout(zm_foot)
        grid.addWidget(self._zm_footer_wrap, 2, 2, 1, 2)

        preset_box = QVBoxLayout()
        self._preset_label = QLabel("Presets")
        preset_lbl = self._preset_label
        preset_lbl.setStyleSheet(MUTED_STYLE)
        preset_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        self._preset_buttons = []
        self._preset_press_timers: dict[int, QTimer] = {}
        self._preset_longpress_fired: dict[int, bool] = {}
        for i in range(3):
            p = QPushButton(str(i + 1))
            p.setObjectName("presetChip")
            p.setCursor(Qt.CursorShape.PointingHandCursor)
            p.setCheckable(True)
            p.setAutoExclusive(True)
            p.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            idx = i
            p.clicked.connect(lambda checked=False, n=idx: self._emit_preset_click_if_not_longpress(n))
            p.customContextMenuRequested.connect(
                lambda _pos, n=idx: self.preset_save_requested.emit(n)
            )
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(700)
            timer.timeout.connect(lambda n=idx: self._on_preset_longpress(n))
            self._preset_press_timers[idx] = timer
            self._preset_longpress_fired[idx] = False
            p.pressed.connect(lambda n=idx: self._on_preset_pressed(n))
            p.released.connect(lambda n=idx: self._on_preset_released(n))
            preset_row.addWidget(p)
            self._preset_buttons.append(p)
        preset_box.addWidget(preset_lbl)
        preset_box.addLayout(preset_row)
        grid.addLayout(preset_box, 0, 4, 3, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)

        self.sync_touch_metrics(1080)

    def sync_touch_metrics(self, short_edge: int) -> None:
        bar_h = _clamp_int(short_edge // 9, 112, 148)
        self.setFixedHeight(bar_h)
        gh = _clamp_int(short_edge // 135, 7, 11)
        hw = _clamp_int(short_edge // 42, 22, 32)
        chip = _clamp_int(short_edge // 21, 50, 64)
        chip_r = chip // 2
        title_pt = _clamp_int(short_edge // 88, 11, 14)
        glyph_pt = _clamp_int(short_edge // 55, 16, 22)
        muted_pt = _clamp_int(short_edge // 100, 9, 11)
        mx = _clamp_int(short_edge // 54, 16, 28)
        my = _clamp_int(short_edge // 108, 8, 14)
        self._grid.setContentsMargins(mx, my, mx, my)
        self._grid.setHorizontalSpacing(_clamp_int(short_edge // 38, 22, 32))
        self._grid.setVerticalSpacing(_clamp_int(short_edge // 180, 5, 8))
        br = _clamp_int(short_edge // 55, 10, 18)
        self.setStyleSheet(
            f"""
            QFrame#BottomControlBar {{
                background-color: {CHROME_BG};
                border: 1px solid {CHROME_BORDER};
                border-radius: {br}px;
            }}
            QLabel#BottomBarGlyph {{
                color: rgba(255,255,255,0.88);
                font-size: {glyph_pt}px;
                font-weight: 500;
            }}
            QLabel#BottomBarGlyphLarge {{
                color: rgba(255,255,255,0.92);
                font-size: {_clamp_int(glyph_pt * 4 // 3, 18, 28)}px;
                font-weight: 500;
            }}
            QPushButton#presetChip {{
                background-color: rgba(255,255,255,0.11);
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: {chip_r}px;
                color: #fff;
                min-width: {chip}px;
                min-height: {chip}px;
                font-weight: 700;
                font-size: {_clamp_int(short_edge // 36, 15, 19)}px;
            }}
            QPushButton#presetChip:hover {{ background-color: rgba(255,255,255,0.2); }}
            QPushButton#presetChip:pressed {{ background-color: rgba(255,255,255,0.26); }}
            QPushButton#presetChip:checked {{
                background-color: rgba(255,255,255,0.26);
                border-color: rgba(255,255,255,0.42);
            }}
            """
        )
        self._br_title.setStyleSheet(
            f"font-weight: 600; color: #fff; font-size: {title_pt}px;"
        )
        self._zm_title.setStyleSheet(
            f"font-weight: 600; color: #fff; font-size: {title_pt}px;"
        )
        self._brightness_slider.set_visual_metrics(hw, gh, _clamp_int(short_edge // 160, 5, 10))
        self._zoom_slider.set_visual_metrics(hw, gh, _clamp_int(short_edge // 160, 5, 10))
        muted = f"color: #b0b0b0; font-size: {muted_pt}px;"
        for lbl in self._br_footer_wrap.findChildren(QLabel):
            lbl.setStyleSheet(muted)
        for lbl in self._zm_footer_wrap.findChildren(QLabel):
            lbl.setStyleSheet(muted)
        self._preset_label.setStyleSheet(muted)
        gw = _clamp_int(short_edge // 30, 32, 44)
        for gl in self.findChildren(QLabel):
            on = gl.objectName()
            if on == "BottomBarGlyph":
                gl.setFixedWidth(gw)
            elif on == "BottomBarGlyphLarge":
                gl.setFixedWidth(_clamp_int(gw * 11 // 9, 40, 56))

    def brightness_percent(self) -> int:
        return self._brightness_slider.value()

    def zoom_percent(self) -> int:
        return self._zoom_slider.value()

    def set_brightness_percent(self, value: int) -> None:
        self._brightness_slider.setValue(max(0, min(100, int(value))))

    def set_zoom_percent(self, value: int) -> None:
        self._zoom_slider.setValue(max(0, min(100, int(value))))

    def set_active_preset(self, index: int) -> None:
        if not hasattr(self, "_preset_buttons"):
            return
        if 0 <= index < len(self._preset_buttons):
            self._preset_buttons[index].setChecked(True)

    def _on_preset_pressed(self, index: int) -> None:
        self._preset_longpress_fired[index] = False
        t = self._preset_press_timers.get(index)
        if t is not None:
            t.start()

    def _on_preset_released(self, index: int) -> None:
        t = self._preset_press_timers.get(index)
        if t is not None and t.isActive():
            t.stop()

    def _on_preset_longpress(self, index: int) -> None:
        self._preset_longpress_fired[index] = True
        self.preset_save_requested.emit(index)

    def _emit_preset_click_if_not_longpress(self, index: int) -> None:
        if self._preset_longpress_fired.get(index, False):
            self._preset_longpress_fired[index] = False
            return
        self.preset_clicked.emit(index)


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
        short = max(480, min(w, h))
        self._top.sync_touch_metrics(short)
        self._right.sync_touch_metrics(short)
        self._bottom.sync_touch_metrics(short)
        th = self._top.height()
        rw = self._right.width()
        bh = self._bottom.height()

        inset = _clamp_int(short // 72, 10, 22)
        gap = _clamp_int(short // 120, 4, 8)
        rail_top = inset + th + gap
        bottom_top = h - bh - inset
        rail_h = max(40, bottom_top - rail_top - gap)

        self._preview.setGeometry(0, 0, w, h)
        self._top.setGeometry(inset, inset, max(0, w - 2 * inset), th)
        self._right.setGeometry(w - rw - inset, rail_top, rw, rail_h)
        self._bottom.setGeometry(inset, bottom_top, max(0, w - 2 * inset), bh)

        preview_h = max(0, bottom_top - rail_top - gap)
        margin = 10
        panel = self._overlay
        panel.adjustSize()
        pw = panel.width()
        ph = panel.height()
        x = w - rw - inset - pw - margin
        y = rail_top + margin
        if x < inset + margin:
            x = inset + margin
        if y + ph > bottom_top - margin:
            y = max(rail_top + margin, bottom_top - ph - margin)
        panel.move(x, y)

        settings_visible = self._settings is not None and self._settings.isVisible()
        if settings_visible:
            # Never stack both floating panels; this causes visual artifacts.
            self._overlay.hide()

        if self._settings is not None and self._settings.isVisible():
            margin_s = 14
            avail_h = max(200, preview_h - 2 * margin_s)
            if hasattr(self._settings, "set_responsive_metrics"):
                self._settings.set_responsive_metrics(
                    w - rw - inset - 2 * margin_s, preview_h
                )
            self._settings.setMaximumHeight(avail_h)
            self._settings.adjustSize()
            sw = self._settings.width()
            sh = min(self._settings.sizeHint().height(), avail_h)
            self._settings.resize(sw, sh)
            sx = max(margin_s + inset, w - rw - inset - sw - margin_s)
            sy = rail_top + margin_s
            if sy + sh > bottom_top - margin_s:
                sy = max(rail_top + margin_s, bottom_top - sh - margin_s)
            self._settings.move(sx, sy)
            self._settings.raise_()
        if not settings_visible and self._overlay.isVisible():
            self._overlay.raise_()
        if self._settings is not None and self._settings.isVisible():
            self._settings.raise_()
        self._top.raise_()
        self._right.raise_()
        self._bottom.raise_()
