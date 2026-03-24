"""
Responsive floating settings panel for the clinical shell.
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
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


def _title(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 28px; font-weight: 700;")
    return w


def _section(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 16px; font-weight: 600;")
    return w


def _label(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet("color: rgba(255,255,255,0.88); font-size: 14px;")
    return w


def _value(text: str, bold: bool = False) -> QLabel:
    wt = 650 if bold else 500
    w = QLabel(text)
    w.setStyleSheet(
        f"color: rgba(255,255,255,0.9); font-size: 14px; font-weight: {wt};"
    )
    return w


def _toggle_switch() -> QCheckBox:
    cb = QCheckBox()
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setStyleSheet(
        """
        QCheckBox::indicator {
            width: 62px;
            height: 30px;
            border-radius: 15px;
            background: rgba(255,255,255,0.28);
            border: 1px solid rgba(255,255,255,0.35);
        }
        QCheckBox::indicator:checked {
            background: rgba(255,255,255,0.56);
            border-color: rgba(255,255,255,0.45);
        }
        """
    )
    return cb


def _pill_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        """
        QPushButton {
            min-height: 34px;
            border-radius: 17px;
            border: 1px solid rgba(255,255,255,0.6);
            background: rgba(255,255,255,0.14);
            color: rgba(255,255,255,0.9);
            font-size: 13px;
            font-weight: 600;
            padding: 0 14px;
        }
        QPushButton:checked {
            background: rgba(255,255,255,0.26);
            border-color: rgba(255,255,255,0.8);
            color: #ffffff;
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
        self._app_name = app_name
        self._app_version = app_version
        self._base_width = 430
        self._content_scale = 1.0

        self.setObjectName("ClinicalSettingsPanel")
        self.setStyleSheet(
            """
            QFrame#ClinicalSettingsPanel {
                background: rgba(125, 100, 100, 0.52);
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: 18px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(8)

        hdr = QHBoxLayout()
        self._title = _title("Settings")
        close_btn = QPushButton("X")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setStyleSheet(
            "QPushButton { color:#fff; font-size: 20px; font-weight:700; border:none; }"
        )
        close_btn.clicked.connect(self.close_requested.emit)
        hdr.addWidget(self._title)
        hdr.addStretch(1)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 4, 4, 8)
        self._body_layout.setSpacing(10)

        self._build_display_section()
        self._build_capture_section()
        self._build_storage_section()
        self._build_about_section()
        self._body_layout.addStretch(1)

        self._scroll.setWidget(body)
        root.addWidget(self._scroll, 1)

        # hidden controls maintain existing setting data flow
        self._quality_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._quality_slider.setRange(60, 100)
        self._quality_slider.setValue(94)
        self._quality_slider.valueChanged.connect(self._on_quality_slider)
        self._led_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._led_slider.setRange(0, 100)
        self._led_slider.setValue(50)
        self._led_slider.valueChanged.connect(self._on_led_slider)

    def _build_display_section(self) -> None:
        self._body_layout.addWidget(_section("Display"))
        self._body_layout.addLayout(self._toggle_row("Show Grid Overlay", "grid"))
        self._body_layout.addLayout(self._toggle_row("Show Crosshair", "crosshair"))
        auto_row = self._toggle_row("Auto Scale Preview", "autoscale")
        self.auto_scale_toggle.setChecked(True)
        self._body_layout.addLayout(auto_row)

    def _build_capture_section(self) -> None:
        self._body_layout.addSpacing(4)
        self._body_layout.addWidget(_section("Capture"))

        scope_head = QHBoxLayout()
        scope_head.addStretch(1)
        scope_head.addWidget(_value("PREVIEW", bold=True))
        scope_head.addStretch(1)
        scope_head.addWidget(_value("Export All", bold=True))
        scope_head.addStretch(1)
        self._body_layout.addLayout(scope_head)

        scope_row = QHBoxLayout()
        self.preview_radio = QPushButton()
        self.full_radio = QPushButton()
        for b in (self.preview_radio, self.full_radio):
            b.setCheckable(True)
            b.setFixedSize(24, 24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border-radius: 12px;
                    border: 2px solid rgba(255,255,255,0.86);
                    background: rgba(255,255,255,0.16);
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.92);
                }
                """
            )
        grp_scope = QButtonGroup(self)
        grp_scope.setExclusive(True)
        grp_scope.addButton(self.preview_radio)
        grp_scope.addButton(self.full_radio)
        self.preview_radio.setChecked(True)
        self.preview_radio.toggled.connect(
            lambda c: c and self.export_scope_changed.emit("preview")
        )
        self.full_radio.toggled.connect(lambda c: c and self.export_scope_changed.emit("full"))
        scope_row.addStretch(1)
        scope_row.addWidget(self.preview_radio)
        scope_row.addStretch(1)
        scope_row.addWidget(self.full_radio)
        scope_row.addStretch(1)
        self._body_layout.addLayout(scope_row)

        fmt = QHBoxLayout()
        fmt.addWidget(_label("Image Format"))
        fmt.addStretch(1)
        self._fmt_jpg = QPushButton("JPG")
        self._fmt_png = QPushButton("PNG")
        for b in (self._fmt_jpg, self._fmt_png):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFlat(True)
            b.setStyleSheet(
                """
                QPushButton {
                    color: rgba(255,255,255,0.74);
                    border: none;
                    background: transparent;
                    font-size: 14px;
                    font-weight: 600;
                    padding: 0 2px;
                }
                QPushButton:checked {
                    color: rgba(255,255,255,0.98);
                }
                """
            )
        grp_fmt = QButtonGroup(self)
        grp_fmt.setExclusive(True)
        grp_fmt.addButton(self._fmt_jpg)
        grp_fmt.addButton(self._fmt_png)
        self._fmt_jpg.setChecked(True)
        self._fmt_jpg.toggled.connect(lambda c: c and self.capture_format_changed.emit("jpg"))
        self._fmt_png.toggled.connect(lambda c: c and self.capture_format_changed.emit("png"))
        fmt.addWidget(self._fmt_jpg)
        fmt.addWidget(self._fmt_png)
        self._body_layout.addLayout(fmt)

        self._body_layout.addLayout(self._value_row("Image Quality", "94%", "quality"))
        self._body_layout.addLayout(self._value_row("LEDs Preset", "50%", "led"))

        mode = QHBoxLayout()
        self.btn_snapshot = _pill_button("SNAPSHOT")
        self.btn_burst = _pill_button("BURST")
        self.btn_snapshot.setChecked(True)
        grp_mode = QButtonGroup(self)
        grp_mode.setExclusive(True)
        grp_mode.addButton(self.btn_snapshot)
        grp_mode.addButton(self.btn_burst)
        self.btn_snapshot.toggled.connect(
            lambda c: c and self.capture_mode_changed.emit("snapshot")
        )
        self.btn_burst.toggled.connect(lambda c: c and self.capture_mode_changed.emit("burst"))
        mode.addWidget(self.btn_snapshot, 1)
        mode.addWidget(self.btn_burst, 1)
        self._body_layout.addLayout(mode)

        delay = QHBoxLayout()
        delay.addWidget(_label("Delay"))
        self._delay_buttons: dict[int, QPushButton] = {}
        self._delay_group = QButtonGroup(self)
        self._delay_group.setExclusive(True)
        for sec in (2, 5, 10, 15, 30, 60):
            b = QPushButton(str(sec))
            b.setCheckable(True)
            b.setFixedSize(32, 32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border-radius: 16px;
                    border: none;
                    background: transparent;
                    color: rgba(255,255,255,0.83);
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.34);
                    color: #fff;
                }
                """
            )
            self._delay_group.addButton(b)
            self._delay_buttons[sec] = b
            delay.addWidget(b)
            b.toggled.connect(lambda c, s=sec: c and self.burst_delay_sec_changed.emit(s))
        self._delay_buttons[10].setChecked(True)
        delay.addStretch(1)
        self._body_layout.addLayout(delay)

        self._body_layout.addLayout(self._toggle_row("Camera Sound", "sound"))

    def _build_storage_section(self) -> None:
        self._body_layout.addSpacing(2)
        self._body_layout.addWidget(_section("Storage"))
        row = QHBoxLayout()
        self.btn_system = _pill_button("SYSTEM")
        self.btn_sd = _pill_button("SD CARD")
        self.btn_system.setChecked(True)
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.btn_system)
        grp.addButton(self.btn_sd)
        self.btn_system.toggled.connect(
            lambda c: c and self.storage_target_changed.emit("system")
        )
        self.btn_sd.toggled.connect(self._on_sd_toggled)
        row.addWidget(self.btn_system, 1)
        row.addWidget(self.btn_sd, 1)
        self._body_layout.addLayout(row)

    def _build_about_section(self) -> None:
        self._body_layout.addSpacing(2)
        self._body_layout.addWidget(_section("About"))
        about = QLabel(f"{self._app_name} ALPHA V1.0    ©2026")
        about.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body_layout.addWidget(about)

    def _toggle_row(self, label: str, kind: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(_label(label))
        row.addStretch(1)
        toggle = _toggle_switch()
        row.addWidget(toggle, 0, Qt.AlignmentFlag.AlignRight)
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
        return row

    def _value_row(self, name: str, value: str, kind: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(_label(name))
        row.addStretch(1)
        val = _value(value)
        row.addWidget(val)
        if kind == "quality":
            self._quality_pct = val
        elif kind == "led":
            self._led_pct = val
            auto = _value("AUTO", bold=True)
            auto.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 14px; font-weight: 700;")
            row.addSpacing(18)
            row.addWidget(auto)
        return row

    def set_responsive_metrics(self, available_width: int, available_height: int) -> None:
        """Scale panel size for current viewport, preserving screenshot-like proportions."""
        w = max(320, min(460, int(available_width * 0.34)))
        h = max(420, min(760, int(available_height * 0.90)))
        self.setFixedWidth(w)
        self.setMaximumHeight(h)
        self.setMinimumHeight(min(380, h))

    def _on_quality_slider(self, value: int) -> None:
        self._quality_pct.setText(f"{value}%")
        self.jpeg_quality_changed.emit(value)

    def _on_led_slider(self, value: int) -> None:
        self._led_pct.setText(f"{value}%")
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
