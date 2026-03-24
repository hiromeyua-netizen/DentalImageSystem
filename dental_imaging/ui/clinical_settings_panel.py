"""
Floating settings panel styled to match the clinical reference screenshot.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

GLASS_BG = "rgba(128, 95, 95, 0.58)"
GLASS_BORDER = "rgba(255,255,255,0.22)"
TEXT = "color: #f2f2f2; font-size: 15px;"
SUB = "color: rgba(240,240,240,0.85); font-size: 14px;"
MUTED = "color: rgba(245,245,245,0.65); font-size: 13px;"


def _row_label(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setStyleSheet(SUB)
    return lab


def _ios_toggle() -> QCheckBox:
    cb = QCheckBox()
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setStyleSheet(
        """
        QCheckBox::indicator {
            width: 78px;
            height: 36px;
            border-radius: 18px;
            background-color: rgba(255,255,255,0.36);
            border: 1px solid rgba(255,255,255,0.35);
        }
        QCheckBox::indicator:checked {
            background-color: rgba(255,255,255,0.58);
            border-color: rgba(255,255,255,0.5);
        }
        """
    )
    return cb


def _capsule(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        """
        QPushButton {
            min-height: 38px;
            border-radius: 19px;
            border: 2px solid rgba(255,255,255,0.55);
            background: rgba(255,255,255,0.15);
            color: rgba(250,250,250,0.94);
            font-size: 13px;
            font-weight: 600;
            padding: 0 14px;
        }
        QPushButton:checked {
            background: rgba(255,255,255,0.3);
            color: #fff;
            border-color: rgba(255,255,255,0.8);
        }
        """
    )
    return b


class ClinicalSettingsPanel(QFrame):
    close_requested = pyqtSignal()
    show_grid_changed = pyqtSignal(bool)
    show_crosshair_changed = pyqtSignal(bool)
    auto_scale_preview_changed = pyqtSignal(bool)
    export_scope_changed = pyqtSignal(str)  # preview | full
    capture_format_changed = pyqtSignal(str)  # jpg | png
    jpeg_quality_changed = pyqtSignal(int)
    led_preset_changed = pyqtSignal(int)
    capture_mode_changed = pyqtSignal(str)  # snapshot | burst
    burst_delay_sec_changed = pyqtSignal(int)
    camera_sound_changed = pyqtSignal(bool)
    storage_target_changed = pyqtSignal(str)  # system | sd
    sd_card_requested = pyqtSignal()

    def __init__(self, app_name: str, app_version: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ClinicalSettingsPanel")
        self.setFixedWidth(490)
        self.setMinimumHeight(780)
        self.setStyleSheet(
            f"""
            QFrame#ClinicalSettingsPanel {{
                background: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 18px;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        t = QLabel("Settings")
        t.setStyleSheet("color:#fff; font-size: 34px; font-weight:700;")
        x = QPushButton("X")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setFlat(True)
        x.setStyleSheet("QPushButton { color:#fff; font-size: 24px; font-weight:700; border:none; }")
        x.clicked.connect(self.close_requested.emit)
        header.addWidget(t)
        header.addStretch(1)
        header.addWidget(x)
        root.addLayout(header)

        # Display
        root.addWidget(_row_label("Display"))
        root.addLayout(self._toggle_row("Show Grid Overlay", "grid"))
        root.addLayout(self._toggle_row("Show Crosshair", "crosshair"))
        auto_row = self._toggle_row("Auto Scale Preview", "autoscale")
        self.auto_scale_toggle.setChecked(True)
        root.addLayout(auto_row)

        # Capture
        root.addSpacing(6)
        root.addWidget(_row_label("Capture"))

        col = QHBoxLayout()
        left = QLabel("PREVIEW")
        left.setStyleSheet(MUTED + " font-weight: 700;")
        right = QLabel("Export All")
        right.setStyleSheet(SUB + " font-weight: 700;")
        col.addStretch(1)
        col.addWidget(left)
        col.addStretch(1)
        col.addWidget(right)
        col.addStretch(1)
        root.addLayout(col)

        scope = QHBoxLayout()
        self.preview_radio = QPushButton(" ")
        self.full_radio = QPushButton(" ")
        for b in (self.preview_radio, self.full_radio):
            b.setCheckable(True)
            b.setFixedSize(26, 26)
            b.setStyleSheet(
                """
                QPushButton {
                    border-radius: 13px;
                    border: 2px solid rgba(255,255,255,0.85);
                    background: rgba(255,255,255,0.18);
                }
                QPushButton:checked { background: rgba(255,255,255,0.9); }
                """
            )
        self.preview_radio.setChecked(True)
        grp_scope = QButtonGroup(self)
        grp_scope.setExclusive(True)
        grp_scope.addButton(self.preview_radio)
        grp_scope.addButton(self.full_radio)
        scope.addStretch(1)
        scope.addWidget(self.preview_radio)
        scope.addStretch(1)
        scope.addWidget(self.full_radio)
        scope.addStretch(1)
        root.addLayout(scope)
        self.preview_radio.toggled.connect(lambda c: c and self.export_scope_changed.emit("preview"))
        self.full_radio.toggled.connect(lambda c: c and self.export_scope_changed.emit("full"))

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(_row_label("Image Format"))
        fmt_row.addStretch(1)
        self._fmt_jpg = QPushButton("JPG")
        self._fmt_png = QPushButton("PNG")
        for b in (self._fmt_jpg, self._fmt_png):
            b.setCheckable(True)
            b.setFlat(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    background: transparent;
                    color: rgba(245,245,245,0.78);
                    font-size: 14px;
                    font-weight: 600;
                    padding: 0 3px;
                }
                QPushButton:checked { color: #ffffff; }
                """
            )
        grp_fmt = QButtonGroup(self)
        grp_fmt.setExclusive(True)
        grp_fmt.addButton(self._fmt_jpg)
        grp_fmt.addButton(self._fmt_png)
        self._fmt_jpg.setChecked(True)
        self._fmt_jpg.toggled.connect(lambda c: c and self.capture_format_changed.emit("jpg"))
        self._fmt_png.toggled.connect(lambda c: c and self.capture_format_changed.emit("png"))
        fmt_row.addWidget(self._fmt_jpg)
        fmt_row.addWidget(self._fmt_png)
        root.addLayout(fmt_row)
        root.addLayout(self._value_row("Image Quality", "94%", "quality"))
        root.addLayout(self._value_row("LEDs Preset", "50%        AUTO", "led"))

        mode = QHBoxLayout()
        self.btn_snapshot = _capsule("SNAPSHOT")
        self.btn_burst = _capsule("BURST")
        self.btn_snapshot.setChecked(True)
        grp_mode = QButtonGroup(self)
        grp_mode.setExclusive(True)
        grp_mode.addButton(self.btn_snapshot)
        grp_mode.addButton(self.btn_burst)
        self.btn_snapshot.toggled.connect(lambda c: c and self.capture_mode_changed.emit("snapshot"))
        self.btn_burst.toggled.connect(lambda c: c and self.capture_mode_changed.emit("burst"))
        mode.addWidget(self.btn_snapshot, 1)
        mode.addWidget(self.btn_burst, 1)
        root.addLayout(mode)

        delay = QHBoxLayout()
        delay.addWidget(_row_label("Delay"))
        self._delay_buttons: dict[int, QPushButton] = {}
        self._delay_group = QButtonGroup(self)
        self._delay_group.setExclusive(True)
        for sec in (2, 5, 10, 15, 30, 60):
            b = QPushButton(str(sec))
            b.setCheckable(True)
            b.setFixedSize(36, 36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border-radius: 18px;
                    border: none;
                    background: transparent;
                    color: rgba(255,255,255,0.86);
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.36);
                    color: #fff;
                }
                """
            )
            self._delay_buttons[sec] = b
            self._delay_group.addButton(b)
            delay.addWidget(b)
            b.toggled.connect(lambda c, s=sec: c and self.burst_delay_sec_changed.emit(s))
        self._delay_buttons[10].setChecked(True)
        delay.addStretch(1)
        root.addLayout(delay)

        root.addLayout(self._toggle_row("Camera Sound", "sound"))

        # Storage
        root.addSpacing(4)
        root.addWidget(_row_label("Storage"))
        stor = QHBoxLayout()
        self.btn_system = _capsule("SYSTEM")
        self.btn_sd = _capsule("SD CARD")
        self.btn_system.setChecked(True)
        grp_st = QButtonGroup(self)
        grp_st.setExclusive(True)
        grp_st.addButton(self.btn_system)
        grp_st.addButton(self.btn_sd)
        self.btn_system.toggled.connect(lambda c: c and self.storage_target_changed.emit("system"))
        self.btn_sd.toggled.connect(self._on_sd_toggled)
        stor.addWidget(self.btn_system, 1)
        stor.addWidget(self.btn_sd, 1)
        root.addLayout(stor)

        # About
        root.addSpacing(6)
        root.addWidget(_row_label("About"))
        about = QLabel(f"{app_name} ALPHA V1.0      ©2026")
        about.setStyleSheet(MUTED)
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(about)
        root.addStretch(1)

        # hidden functional controls to keep settings behavior
        self._quality_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._quality_slider.setRange(60, 100)
        self._quality_slider.setValue(94)
        self._quality_slider.valueChanged.connect(self._on_quality_slider)
        self._led_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._led_slider.setRange(0, 100)
        self._led_slider.setValue(50)
        self._led_slider.valueChanged.connect(self._on_led_slider)

    def _toggle_row(self, label: str, kind: str) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(_row_label(label))
        h.addStretch(1)
        toggle = _ios_toggle()
        h.addWidget(toggle, 0, Qt.AlignmentFlag.AlignRight)
        if kind == "grid":
            self.show_grid_toggle = toggle
            self.show_grid_toggle.toggled.connect(self.show_grid_changed.emit)
        elif kind == "crosshair":
            self.show_crosshair_toggle = toggle
            self.show_crosshair_toggle.toggled.connect(self.show_crosshair_changed.emit)
        elif kind == "autoscale":
            self.auto_scale_toggle = toggle
            self.auto_scale_toggle.toggled.connect(self.auto_scale_preview_changed.emit)
        else:
            self.camera_sound_toggle = toggle
            self.camera_sound_toggle.toggled.connect(self.camera_sound_changed.emit)
        return h

    def _value_row(self, left: str, right: str, kind: str) -> QHBoxLayout:
        h = QHBoxLayout()
        h.addWidget(_row_label(left))
        h.addStretch(1)
        value = QLabel(right)
        value.setStyleSheet(SUB)
        h.addWidget(value)
        if kind == "quality":
            self._quality_pct = value
        elif kind == "led":
            self._led_pct = value
        return h

    def _on_quality_slider(self, value: int) -> None:
        self._quality_pct.setText(f"{value}%")
        self.jpeg_quality_changed.emit(value)

    def _on_led_slider(self, value: int) -> None:
        self._led_pct.setText(f"{value}%        AUTO")
        self.led_preset_changed.emit(value)

    def _on_sd_toggled(self, checked: bool) -> None:
        if checked:
            self.storage_target_changed.emit("sd")
            self.sd_card_requested.emit()

    def sync_from_main_window(
        self,
        *,
        show_grid: bool,
        show_crosshair: bool,
        auto_scale: bool,
        export_full_resolution: bool,
        image_format: str,
        jpeg_quality: int,
        capture_mode_burst: bool,
        burst_delay_sec: int,
        camera_sound: bool,
        storage_sd_selected: bool,
    ) -> None:
        self.show_grid_toggle.blockSignals(True)
        self.show_crosshair_toggle.blockSignals(True)
        self.auto_scale_toggle.blockSignals(True)
        self.show_grid_toggle.setChecked(show_grid)
        self.show_crosshair_toggle.setChecked(show_crosshair)
        self.auto_scale_toggle.setChecked(auto_scale)
        self.show_grid_toggle.blockSignals(False)
        self.show_crosshair_toggle.blockSignals(False)
        self.auto_scale_toggle.blockSignals(False)

        self.preview_radio.blockSignals(True)
        self.full_radio.blockSignals(True)
        self.full_radio.setChecked(export_full_resolution)
        self.preview_radio.setChecked(not export_full_resolution)
        self.preview_radio.blockSignals(False)
        self.full_radio.blockSignals(False)

        fmt = (image_format or "png").lower()
        self._fmt_jpg.blockSignals(True)
        self._fmt_png.blockSignals(True)
        self._fmt_jpg.setChecked(fmt in ("jpg", "jpeg"))
        self._fmt_png.setChecked(fmt not in ("jpg", "jpeg"))
        self._fmt_jpg.blockSignals(False)
        self._fmt_png.blockSignals(False)

        self._quality_slider.blockSignals(True)
        self._quality_slider.setValue(jpeg_quality)
        self._quality_slider.blockSignals(False)
        self._quality_pct.setText(f"{jpeg_quality}%")

        self.btn_snapshot.blockSignals(True)
        self.btn_burst.blockSignals(True)
        self.btn_burst.setChecked(capture_mode_burst)
        self.btn_snapshot.setChecked(not capture_mode_burst)
        self.btn_snapshot.blockSignals(False)
        self.btn_burst.blockSignals(False)

        for sec, btn in self._delay_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(sec == burst_delay_sec)
            btn.blockSignals(False)

        self.camera_sound_toggle.blockSignals(True)
        self.camera_sound_toggle.setChecked(camera_sound)
        self.camera_sound_toggle.blockSignals(False)

        self.btn_system.blockSignals(True)
        self.btn_sd.blockSignals(True)
        self.btn_sd.setChecked(storage_sd_selected)
        self.btn_system.setChecked(not storage_sd_selected)
        self.btn_system.blockSignals(False)
        self.btn_sd.blockSignals(False)
