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
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dental_imaging.ui.widgets.image_settings_component import ImageSettingsComponent
from dental_imaging.ui.widgets.preview_widget import PreviewWidget

# Chrome constants — translucent dark strip matching the Occuscope reference
CHROME_BG   = "rgba(20, 22, 26, 0.58)"
CHROME_BORDER = "rgba(255, 255, 255, 0.09)"
LABEL_STYLE = "color: #f2f2f2; font-size: 12px;"
TITLE_STYLE = "color: #ffffff; font-weight: 700; font-size: 13px; letter-spacing: 0.5px;"
MUTED_STYLE = "color: #a0a0a8; font-size: 9px; letter-spacing: 0.3px;"


def _clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Custom slider with value painted inside the circular thumb
# ---------------------------------------------------------------------------

class ClinicalValueSlider(QWidget):
    """
    Horizontal slider where a filled circle shows the current value as a
    percentage label — matching the Occuscope bottom-bar style.
    """

    valueChanged = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._value   = 0
        self._minimum = 0
        self._maximum = 100
        self._handle_r = 18
        self._groove_h = 5
        self._dragging = False
        self.setMinimumHeight(self._handle_r * 2 + 8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_visual_metrics(self, handle_r: int, groove_h: int) -> None:
        self._handle_r = max(12, handle_r)
        self._groove_h = max(3, groove_h)
        self.setMinimumHeight(self._handle_r * 2 + 8)
        self.update()

    def value(self) -> int:
        return self._value

    def setValue(self, v: int) -> None:
        v = _clamp_int(v, self._minimum, self._maximum)
        if v != self._value:
            self._value = v
            self.update()
            self.valueChanged.emit(v)

    def setRange(self, lo: int, hi: int) -> None:
        self._minimum, self._maximum = lo, hi
        self._value = _clamp_int(self._value, lo, hi)

    def _cx_from_value(self) -> int:
        hr = self._handle_r
        mx = hr + 2
        span = self._maximum - self._minimum
        frac = (self._value - self._minimum) / span if span > 0 else 0.0
        track_w = max(0, self.width() - 2 * mx)
        return int(round(mx + frac * track_w))

    def _value_from_x(self, x: int) -> int:
        hr = self._handle_r
        mx = hr + 2
        track_w = max(1, self.width() - 2 * mx)
        frac = _clamp_int(x - mx, 0, track_w) / track_w
        return int(round(self._minimum + frac * (self._maximum - self._minimum)))

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        hr = self._handle_r
        gh = self._groove_h
        mx = hr + 2
        gw = max(1, w - 2 * mx)
        gy = (h - gh) // 2

        # Groove
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 38)))
        painter.drawRoundedRect(mx, gy, gw, gh, gh // 2, gh // 2)

        cx = self._cx_from_value()
        cy = h // 2

        # Thumb — white circle
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(QPen(QColor(180, 180, 180, 80), 1))
        painter.drawEllipse(QPointF(cx, cy), float(hr), float(hr))

        # Value label inside thumb
        painter.setPen(QPen(QColor(30, 30, 35)))
        f = self.font()
        f.setPixelSize(_clamp_int(hr - 5, 8, 13))
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(
            QRectF(cx - hr, cy - hr, 2 * hr, 2 * hr),
            int(Qt.AlignmentFlag.AlignCenter),
            f"{self._value}%",
        )

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.setValue(self._value_from_x(ev.pos().x()))

    def mouseMoveEvent(self, ev) -> None:
        if self._dragging:
            self.setValue(self._value_from_x(ev.pos().x()))

    def mouseReleaseEvent(self, ev) -> None:
        self._dragging = False

    def minimumSizeHint(self) -> QSize:
        return QSize(self._handle_r * 6, self._handle_r * 2 + 8)


# ---------------------------------------------------------------------------
# Top status bar
# ---------------------------------------------------------------------------

class TopStatusBar(QFrame):
    """Brand (left), stream stats (centre), CONNECTED pill + power button (right)."""

    power_clicked = pyqtSignal()

    def __init__(self, brand_title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopStatusBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(56)
        self._apply_chrome_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(16)

        # --- Brand ---
        brand_parts = brand_title.split(" — ", 1) if " — " in brand_title else [brand_title, ""]
        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        brand_col.setContentsMargins(0, 0, 0, 0)
        self._brand_main = QLabel(brand_parts[0].upper())
        self._brand_main.setStyleSheet(TITLE_STYLE)
        f = QFont()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        self._brand_main.setFont(f)
        brand_col.addWidget(self._brand_main)
        if brand_parts[1]:
            self._brand_sub = QLabel(brand_parts[1].upper())
            self._brand_sub.setStyleSheet(MUTED_STYLE)
            brand_col.addWidget(self._brand_sub)
        else:
            self._brand_sub = None
        layout.addLayout(brand_col)

        layout.addStretch(1)

        # --- Stats (plain text, no pill) ---
        self._stats = QLabel("— X —     — fps     — MB/s")
        self._stats.setStyleSheet(
            "color: #e8e8e8; font-size: 12px; font-weight: 500; letter-spacing: 0.4px;"
        )
        layout.addWidget(self._stats, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addSpacing(12)

        # --- CONNECTED pill ---
        self._connected = QPushButton("DISCONNECTED")
        self._connected.setObjectName("ConnectedPill")
        self._connected.setCheckable(True)
        self._connected.setChecked(False)
        self._connected.setEnabled(False)
        self._connected.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._connected, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addSpacing(6)

        # --- Power button (circle) ---
        self._power = QPushButton("\u23FB")
        self._power.setObjectName("TopPowerButton")
        self._power.setToolTip("Connect")
        self._power.setCursor(Qt.CursorShape.PointingHandCursor)
        self._power.setFixedSize(44, 44)
        self._power.clicked.connect(self.power_clicked.emit)
        layout.addWidget(self._power, 0, Qt.AlignmentFlag.AlignVCenter)

        self.sync_touch_metrics(1080)

    def _apply_chrome_style(self) -> None:
        self.setStyleSheet(
            f"""
            QFrame#TopStatusBar {{
                background-color: {CHROME_BG};
                border-bottom: 1px solid {CHROME_BORDER};
            }}
            """
        )

    # ------------------------------------------------------------------

    def set_stats_text(self, width: int, height: int, fps: float, mbps: float) -> None:
        self._stats.setText(
            f"{width} X {height}     {fps:.0f} fps     {mbps:.1f} MB/s"
        )

    def set_connected(self, connected: bool) -> None:
        self._connected.setEnabled(True)
        self._connected.setChecked(connected)
        self._connected.setText("CONNECTED" if connected else "DISCONNECTED")

    def set_power_primary_text(self, text: str) -> None:
        self._power.setToolTip(text)

    def sync_touch_metrics(self, short_edge: int) -> None:
        h = _clamp_int(short_edge // 18, 54, 68)
        self.setFixedHeight(h)

        title_pt = _clamp_int(short_edge // 83, 12, 16)
        sub_pt   = _clamp_int(short_edge // 108, 8, 11)
        stat_pt  = _clamp_int(short_edge // 88, 11, 14)
        pill_pt  = _clamp_int(short_edge // 95, 10, 13)
        pill_r   = _clamp_int(short_edge // 50, 14, 24)
        pw       = _clamp_int(short_edge // 22, 40, 54)
        pwr_pt   = _clamp_int(short_edge // 52, 16, 24)

        self._brand_main.setStyleSheet(
            f"color: #ffffff; font-weight: 700; font-size: {title_pt}px; letter-spacing: 0.8px;"
        )
        if self._brand_sub is not None:
            self._brand_sub.setStyleSheet(
                f"color: #a8a8b0; font-size: {sub_pt}px; letter-spacing: 0.3px;"
            )
        self._stats.setStyleSheet(
            f"color: #e8e8e8; font-size: {stat_pt}px; font-weight: 500; letter-spacing: 0.4px;"
        )
        self._connected.setStyleSheet(
            f"""
            QPushButton#ConnectedPill {{
                background-color: rgba(255, 255, 255, 0.10);
                color: #d8d8d8;
                border: 1px solid rgba(255, 255, 255, 0.28);
                border-radius: {pill_r}px;
                padding: 5px 16px;
                font-size: {pill_pt}px;
                font-weight: 700;
                min-height: 26px;
                letter-spacing: 0.5px;
            }}
            QPushButton#ConnectedPill:checked {{
                background-color: rgba(255, 255, 255, 0.18);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.55);
            }}
            QPushButton#ConnectedPill:hover {{
                background-color: rgba(255, 255, 255, 0.16);
            }}
            """
        )
        self._power.setFixedSize(pw, pw)
        self._power.setStyleSheet(
            f"""
            QPushButton#TopPowerButton {{
                background-color: rgba(255, 255, 255, 0.92);
                color: #18181c;
                border: none;
                border-radius: {pw // 2}px;
                font-size: {pwr_pt}px;
                font-weight: 700;
            }}
            QPushButton#TopPowerButton:hover  {{ background-color: #ffffff; }}
            QPushButton#TopPowerButton:pressed {{ background-color: #e0e0e6; }}
            """
        )


# ---------------------------------------------------------------------------
# Right tool rail  (icon-only, no text labels)
# ---------------------------------------------------------------------------

class RightToolRail(QFrame):
    """Narrow vertical icon column — reference Occuscope style (icons only)."""

    flip_vertical_clicked   = pyqtSignal()
    flip_horizontal_clicked = pyqtSignal()
    rotate_ccw_clicked      = pyqtSignal()
    rotate_cw_clicked       = pyqtSignal()
    image_settings_clicked  = pyqtSignal(bool)
    settings_toggled        = pyqtSignal(bool)
    capture_clicked         = pyqtSignal()
    auto_color_toggled      = pyqtSignal(bool)
    recenter_roi_clicked    = pyqtSignal()
    roi_mode_toggled        = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RightToolRail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        self._root_layout = root
        root.setContentsMargins(8, 14, 8, 14)
        root.setSpacing(6)

        def btn(glyph: str, tip: str, checkable: bool = False, checked: bool = False) -> QToolButton:
            b = QToolButton()
            b.setText(glyph)
            b.setToolTip(tip)
            b.setCheckable(checkable)
            b.setChecked(checked)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            return b

        # Flip
        b_fh = btn("\u2194", "Flip horizontal")
        b_fh.clicked.connect(self.flip_horizontal_clicked.emit)
        b_fv = btn("\u2195", "Flip vertical")
        b_fv.clicked.connect(self.flip_vertical_clicked.emit)

        # Rotate
        b_rcw = btn("\u21BB", "Rotate clockwise")
        b_rcw.clicked.connect(self.rotate_cw_clicked.emit)
        b_rcc = btn("\u21BA", "Rotate counter-clockwise")
        b_rcc.clicked.connect(self.rotate_ccw_clicked.emit)

        # Image settings
        self._img_settings = btn("\u25A3", "Image settings", checkable=True, checked=True)
        self._img_settings.toggled.connect(self.image_settings_clicked.emit)

        # Settings
        self._settings_btn = btn("\u2699", "Settings", checkable=True)
        self._settings_btn.toggled.connect(self.settings_toggled.emit)

        # Capture
        self._capture_btn = btn("\u2316", "Capture image")
        self._capture_btn.clicked.connect(self.capture_clicked.emit)

        # Auto colour
        self._auto_color_btn = btn("\u25CE", "Auto colour balance", checkable=True)
        self._auto_color_btn.setObjectName("autoColorBtn")
        self._auto_color_btn.toggled.connect(self.auto_color_toggled.emit)

        # Recenter ROI
        b_rcenter = btn("\u2295", "Recenter ROI")
        b_rcenter.clicked.connect(self.recenter_roi_clicked.emit)

        # ROI mode
        self._roi_mode_btn = btn("\u229E", "ROI mode", checkable=True)
        self._roi_mode_btn.setObjectName("roiModeBtn")
        self._roi_mode_btn.toggled.connect(self.roi_mode_toggled.emit)

        # Pair buttons side-by-side in a row; single buttons centred
        def pair_row(b1: QToolButton, b2: QToolButton) -> None:
            hl = QHBoxLayout()
            hl.setSpacing(6)
            hl.addWidget(b1)
            hl.addWidget(b2)
            root.addLayout(hl)

        def solo_row(b: QToolButton) -> None:
            hl = QHBoxLayout()
            hl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            hl.addWidget(b)
            root.addLayout(hl)

        pair_row(b_fh, b_fv)
        pair_row(b_rcw, b_rcc)
        solo_row(self._img_settings)
        solo_row(self._settings_btn)
        solo_row(self._capture_btn)
        solo_row(self._auto_color_btn)
        solo_row(b_rcenter)
        solo_row(self._roi_mode_btn)
        root.addStretch(1)

        self.sync_touch_metrics(1080)

    # ------------------------------------------------------------------
    def image_settings_button(self) -> QToolButton:  return self._img_settings
    def settings_tool_button(self) -> QToolButton:   return self._settings_btn
    def auto_color_button(self) -> QToolButton:      return self._auto_color_btn
    def roi_mode_button(self) -> QToolButton:        return self._roi_mode_btn

    def set_capture_enabled(self, enabled: bool) -> None:
        self._capture_btn.setEnabled(enabled)

    def sync_touch_metrics(self, short_edge: int) -> None:
        rw      = _clamp_int(short_edge // 11, 72, 96)
        btn_sz  = _clamp_int(short_edge // 24, 36, 50)
        pad     = _clamp_int(short_edge // 150, 4, 8)
        radius  = _clamp_int(short_edge // 160, 6, 10)
        icon_pt = _clamp_int(short_edge // 72, 14, 20)
        self.setFixedWidth(rw)
        self.setStyleSheet(
            f"""
            QFrame#RightToolRail {{
                background-color: {CHROME_BG};
                border-left: 1px solid {CHROME_BORDER};
            }}
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: {radius}px;
                color: rgba(255, 255, 255, 0.80);
                font-size: {icon_pt}px;
                padding: {pad}px;
                min-width:  {btn_sz}px;
                min-height: {btn_sz}px;
            }}
            QToolButton:hover   {{ background-color: rgba(255,255,255,0.10);
                                   color: #ffffff; }}
            QToolButton:pressed {{ background-color: rgba(255,255,255,0.18); }}
            QToolButton:checked {{
                background-color: rgba(255,255,255,0.14);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,0.25);
            }}
            QToolButton#autoColorBtn:checked {{
                background-color: rgba(90,170,110,0.40);
                border-color: rgba(140,220,160,0.50);
                color: #cfffcf;
            }}
            QToolButton#roiModeBtn:checked {{
                background-color: rgba(90,140,220,0.38);
                border-color: rgba(140,180,255,0.48);
                color: #d0deff;
            }}
            """
        )
        spacing = _clamp_int(short_edge // 100, 4, 8)
        mx = _clamp_int(short_edge // 130, 6, 12)
        my = _clamp_int(short_edge // 75, 10, 18)
        self._root_layout.setContentsMargins(mx, my, mx, my)
        self._root_layout.setSpacing(spacing)


# ---------------------------------------------------------------------------
# Bottom control bar
# ---------------------------------------------------------------------------

class BottomControlBar(QFrame):
    """Brightness + zoom sliders with icon bookends, plus preset chips."""

    brightness_changed   = pyqtSignal(int)
    zoom_changed         = pyqtSignal(int)
    preset_clicked       = pyqtSignal(int)
    preset_save_requested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomControlBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Main layout: HBox with [brightness section] [zoom section] [presets]
        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 8, 20, 10)
        outer.setSpacing(32)
        self._outer = outer

        def glyph_label(text: str, large: bool = False) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("GlyphLarge" if large else "GlyphSmall")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return lbl

        def slider_section(
            left_text: str, right_text: str,
            right_large: bool, default: int
        ) -> tuple[QHBoxLayout, ClinicalValueSlider]:
            sl = ClinicalValueSlider()
            sl.setRange(0, 100)
            sl.setValue(default)
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(glyph_label(left_text), 0, Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(sl, 1)
            row.addWidget(
                glyph_label(right_text, large=right_large),
                0, Qt.AlignmentFlag.AlignVCenter,
            )
            return row, sl

        br_row, self._brightness_slider = slider_section(
            "\u2600", "\u2600", right_large=True, default=50
        )
        self._brightness_slider.valueChanged.connect(self.brightness_changed.emit)

        zm_row, self._zoom_slider = slider_section(
            "\u2296", "\u2295", right_large=False, default=0
        )
        self._zoom_slider.valueChanged.connect(self.zoom_changed.emit)

        br_wrap = QWidget()
        br_wrap.setLayout(br_row)
        zm_wrap = QWidget()
        zm_wrap.setLayout(zm_row)

        outer.addWidget(br_wrap, 3)
        outer.addWidget(zm_wrap, 3)

        # Preset chips  ① ② ③
        preset_col = QVBoxLayout()
        preset_col.setSpacing(4)
        self._preset_label = QLabel("Presets")
        self._preset_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)

        self._preset_buttons: list[QPushButton] = []
        self._preset_press_timers: dict[int, QTimer] = {}
        self._preset_longpress_fired: dict[int, bool] = {}

        circled = ["\u2460", "\u2461", "\u2462"]   # ① ② ③
        for i in range(3):
            p = QPushButton(circled[i])
            p.setObjectName("presetChip")
            p.setCursor(Qt.CursorShape.PointingHandCursor)
            p.setCheckable(True)
            p.setAutoExclusive(True)
            p.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            idx = i
            p.clicked.connect(
                lambda _checked=False, n=idx: self._emit_preset_click_if_not_longpress(n)
            )
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

        preset_col.addWidget(self._preset_label)
        preset_col.addLayout(preset_row)
        preset_col.addStretch(1)
        outer.addLayout(preset_col)

        self.sync_touch_metrics(1080)

    # ------------------------------------------------------------------

    def sync_touch_metrics(self, short_edge: int) -> None:
        bar_h      = _clamp_int(short_edge // 10, 90, 124)
        gh         = _clamp_int(short_edge // 145, 4, 8)
        hr         = _clamp_int(short_edge // 44, 18, 28)
        chip       = _clamp_int(short_edge // 22, 44, 58)
        chip_r     = chip // 2
        chip_pt    = _clamp_int(short_edge // 32, 16, 22)
        glyph_sm   = _clamp_int(short_edge // 62, 14, 20)
        glyph_lg   = _clamp_int(short_edge // 46, 18, 26)
        muted_pt   = _clamp_int(short_edge // 105, 9, 11)
        mx         = _clamp_int(short_edge // 54, 14, 26)
        my         = _clamp_int(short_edge // 110, 6, 12)

        self.setFixedHeight(bar_h)
        self._outer.setContentsMargins(mx, my, mx, my)
        self._outer.setSpacing(_clamp_int(short_edge // 34, 24, 40))

        self.setStyleSheet(
            f"""
            QFrame#BottomControlBar {{
                background-color: {CHROME_BG};
                border-top: 1px solid {CHROME_BORDER};
            }}
            QLabel#GlyphSmall {{
                color: rgba(255,255,255,0.80);
                font-size: {glyph_sm}px;
            }}
            QLabel#GlyphLarge {{
                color: rgba(255,255,255,0.90);
                font-size: {glyph_lg}px;
            }}
            QPushButton#presetChip {{
                background-color: transparent;
                border: 2px solid rgba(255,255,255,0.45);
                border-radius: {chip_r}px;
                color: rgba(255,255,255,0.80);
                min-width:  {chip}px;
                min-height: {chip}px;
                font-size: {chip_pt}px;
                font-weight: 400;
            }}
            QPushButton#presetChip:hover {{
                background-color: rgba(255,255,255,0.10);
                color: #ffffff;
            }}
            QPushButton#presetChip:checked {{
                background-color: rgba(255,255,255,0.18);
                border-color: rgba(255,255,255,0.80);
                color: #ffffff;
            }}
            """
        )
        for sl in (self._brightness_slider, self._zoom_slider):
            sl.set_visual_metrics(hr, gh)
        self._preset_label.setStyleSheet(
            f"color: #a0a0a8; font-size: {muted_pt}px; letter-spacing: 0.3px;"
        )

    # ------------------------------------------------------------------

    def brightness_percent(self) -> int:
        return self._brightness_slider.value()

    def zoom_percent(self) -> int:
        return self._zoom_slider.value()

    def set_brightness_percent(self, value: int) -> None:
        self._brightness_slider.setValue(max(0, min(100, int(value))))

    def set_zoom_percent(self, value: int) -> None:
        self._zoom_slider.setValue(max(0, min(100, int(value))))

    def set_active_preset(self, index: int) -> None:
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


# ---------------------------------------------------------------------------
# Full-bleed viewport (preview fills 100%, chrome overlaid at edges)
# ---------------------------------------------------------------------------

class ClinicalViewport(QWidget):
    """
    Full-bleed live preview with overlaid chrome: top bar (full width), right
    rail (right edge), bottom bar (left of rail) — Occuscope layout.
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
        self._preview  = preview
        self._overlay  = image_settings
        self._settings = settings_panel
        self._top    = TopStatusBar(brand_title, self)
        self._right  = RightToolRail(self)
        self._bottom = BottomControlBar(self)

        preview.setParent(self)
        image_settings.setParent(self)
        self._top.setParent(self)
        self._right.setParent(self)
        self._bottom.setParent(self)
        if self._settings is not None:
            self._settings.setParent(self)
            self._settings.hide()

        # Stacking order: preview at back, chrome on top
        self._top.raise_()
        self._right.raise_()
        self._bottom.raise_()
        image_settings.raise_()
        if self._settings is not None:
            self._settings.raise_()

    # ------------------------------------------------------------------
    def top_bar(self)     -> TopStatusBar:     return self._top
    def right_rail(self)  -> RightToolRail:    return self._right
    def bottom_bar(self)  -> BottomControlBar: return self._bottom
    def preview_widget(self) -> PreviewWidget: return self._preview
    def settings_panel(self) -> Optional[QWidget]: return self._settings

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.layout_chrome()

    def layout_chrome(self) -> None:
        """Edge-flush overlay layout matching the Occuscope reference."""
        w, h = self.width(), self.height()
        short = max(480, min(w, h))

        # Update scale-dependent metrics first so fixed sizes are correct
        self._top.sync_touch_metrics(short)
        self._right.sync_touch_metrics(short)
        self._bottom.sync_touch_metrics(short)

        th = self._top.height()
        rw = self._right.width()
        bh = self._bottom.height()

        # Preview fills the full viewport (chrome is overlaid on top)
        self._preview.setGeometry(0, 0, w, h)

        # Top bar: full width at top edge
        self._top.setGeometry(0, 0, w, th)

        # Right rail: right edge, between top bar and bottom bar
        rail_top = th
        rail_h   = max(40, h - th - bh)
        self._right.setGeometry(w - rw, rail_top, rw, rail_h)

        # Bottom bar: full width minus the rail, at bottom edge
        self._bottom.setGeometry(0, h - bh, w - rw, bh)

        # --- Floating image-settings overlay ---
        preview_w = w - rw
        margin = 12
        panel = self._overlay
        panel.adjustSize()
        pw, ph = panel.width(), panel.height()
        x = preview_w - pw - margin
        y = th + margin
        if x < margin:
            x = margin
        if y + ph > h - bh - margin:
            y = max(th + margin, h - bh - ph - margin)
        panel.move(x, y)

        settings_visible = self._settings is not None and self._settings.isVisible()
        if settings_visible:
            self._overlay.hide()   # mutual exclusion

        if self._settings is not None and self._settings.isVisible():
            margin_s = 14
            avail_h  = max(200, h - th - bh - 2 * margin_s)
            if hasattr(self._settings, "set_responsive_metrics"):
                self._settings.set_responsive_metrics(preview_w - 2 * margin_s, h - th - bh)
            self._settings.setMaximumHeight(avail_h)
            self._settings.adjustSize()
            sw = self._settings.width()
            sh = min(self._settings.sizeHint().height(), avail_h)
            self._settings.resize(sw, sh)
            sx = max(margin_s, preview_w - sw - margin_s)
            sy = th + margin_s
            if sy + sh > h - bh - margin_s:
                sy = max(th + margin_s, h - bh - sh - margin_s)
            self._settings.move(sx, sy)
            self._settings.raise_()

        if not settings_visible and self._overlay.isVisible():
            self._overlay.raise_()
        if self._settings is not None and self._settings.isVisible():
            self._settings.raise_()
        self._top.raise_()
        self._right.raise_()
        self._bottom.raise_()
