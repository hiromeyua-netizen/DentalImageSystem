"""
Settings panel styled to match the clinical reference.
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
    QVBoxLayout,
)


def _section(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 12px; font-weight: 700;")
    return w


def _label(text: str) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet("color: rgba(255,255,255,0.88); font-size: 11px;")
    return w


def _value(text: str, weight: int = 600) -> QLabel:
    w = QLabel(text)
    w.setStyleSheet(
        f"color: rgba(255,255,255,0.90); font-size: 11px; font-weight: {weight};"
    )
    return w


def _toggle() -> QCheckBox:
    cb = QCheckBox()
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setStyleSheet(
        """
        QCheckBox::indicator {
            width: 42px;
            height: 22px;
            border-radius: 11px;
            background: rgba(255,255,255,0.32);
            border: 1px solid rgba(255,255,255,0.30);
        }
        QCheckBox::indicator:checked {
            background: rgba(255,255,255,0.62);
            border-color: rgba(255,255,255,0.45);
        }
        """
    )
    return cb


def _pill(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCheckable(True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        """
        QPushButton {
            min-height: 26px;
            border-radius: 13px;
            border: 1px solid rgba(255,255,255,0.58);
            background: rgba(255,255,255,0.12);
            color: rgba(255,255,255,0.92);
            font-size: 10px;
            font-weight: 600;
            padding: 0 10px;
        }
        QPushButton:checked {
            background: rgba(255,255,255,0.22);
            border-color: rgba(255,255,255,0.78);
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

    def __init__(self, app_name: str, app_version: str, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self._app_name = app_name
        self._app_version = app_version
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.setObjectName("ClinicalSettingsPanel")
        self.setStyleSheet(
            """
            QFrame#ClinicalSettingsPanel {
                background: rgba(164, 132, 132, 0.48);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 16px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # header
        hdr = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("color: rgba(255,255,255,0.96); font-size: 17px; font-weight: 700;")
        close_btn = QPushButton("X")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setStyleSheet(
            "QPushButton { color: rgba(255,255,255,0.92); font-size: 16px; font-weight: 700; border: none; }"
        )
        close_btn.clicked.connect(self.close_requested.emit)
        hdr.addWidget(title)
        hdr.addStretch(1)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        # display
        root.addWidget(_section("Display"))
        root.addLayout(self._toggle_row("Show Grid Overlay", "grid"))
        root.addLayout(self._toggle_row("Show Crosshair", "crosshair"))
        auto_row = self._toggle_row("Auto Scale Preview", "autoscale")
        self.auto_scale_toggle.setChecked(True)
        root.addLayout(auto_row)

        # capture
        root.addSpacing(2)
        root.addWidget(_section("Capture"))
        cap_hdr = QHBoxLayout()
        cap_hdr.addStretch(1)
        cap_hdr.addWidget(_value("PREVIEW", 700))
        cap_hdr.addStretch(1)
        cap_hdr.addWidget(_value("Export All", 700))
        cap_hdr.addStretch(1)
        root.addLayout(cap_hdr)

        cap_sel = QHBoxLayout()
        self.preview_radio = QPushButton()
        self.full_radio = QPushButton()
        for b in (self.preview_radio, self.full_radio):
            b.setCheckable(True)
            b.setFixedSize(18, 18)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border-radius: 9px;
                    border: 2px solid rgba(255,255,255,0.8);
                    background: rgba(255,255,255,0.12);
                }
                QPushButton:checked { background: rgba(255,255,255,0.88); }
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
        cap_sel.addStretch(1)
        cap_sel.addWidget(self.preview_radio)
        cap_sel.addStretch(1)
        cap_sel.addWidget(self.full_radio)
        cap_sel.addStretch(1)
        root.addLayout(cap_sel)

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
                    border: none;
                    background: transparent;
                    color: rgba(255,255,255,0.76);
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 2px;
                }
                QPushButton:checked { color: rgba(255,255,255,0.96); }
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
        root.addLayout(fmt)

        root.addLayout(self._value_row("Image Quality", "94%", with_auto=False))
        root.addLayout(self._value_row("LEDs Preset", "50%", with_auto=True))

        modes = QHBoxLayout()
        self.btn_snapshot = _pill("SNAPSHOT")
        self.btn_burst = _pill("BURST")
        grp_mode = QButtonGroup(self)
        grp_mode.setExclusive(True)
        grp_mode.addButton(self.btn_snapshot)
        grp_mode.addButton(self.btn_burst)
        self.btn_snapshot.setChecked(True)
        self.btn_snapshot.toggled.connect(
            lambda c: c and self.capture_mode_changed.emit("snapshot")
        )
        self.btn_burst.toggled.connect(lambda c: c and self.capture_mode_changed.emit("burst"))
        modes.addWidget(self.btn_snapshot, 1)
        modes.addWidget(self.btn_burst, 1)
        root.addLayout(modes)

        delay = QHBoxLayout()
        delay.addWidget(_label("Delay"))
        self._delay_buttons: dict[int, QPushButton] = {}
        self._delay_group = QButtonGroup(self)
        self._delay_group.setExclusive(True)
        for sec in (2, 5, 10, 15, 30, 60):
            b = QPushButton(str(sec))
            b.setCheckable(True)
            b.setFixedSize(22, 22)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 11px;
                    background: transparent;
                    color: rgba(255,255,255,0.86);
                    font-size: 10px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.32);
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
        root.addLayout(delay)

        root.addLayout(self._toggle_row("Camera Sound", "sound"))

        # storage
        root.addSpacing(2)
        root.addWidget(_section("Storage"))
        st = QHBoxLayout()
        self.btn_system = _pill("SYSTEM")
        self.btn_sd = _pill("SD CARD")
        grp_st = QButtonGroup(self)
        grp_st.setExclusive(True)
        grp_st.addButton(self.btn_system)
        grp_st.addButton(self.btn_sd)
        self.btn_system.setChecked(True)
        self.btn_system.toggled.connect(
            lambda c: c and self.storage_target_changed.emit("system")
        )
        self.btn_sd.toggled.connect(self._on_sd_toggled)
        st.addWidget(self.btn_system, 1)
        st.addWidget(self.btn_sd, 1)
        root.addLayout(st)

        root.addSpacing(1)
        root.addWidget(_section("About"))
        about = QLabel(f"{self._app_name} ALPHA V1.0    ©2026")
        about.setStyleSheet("color: rgba(255,255,255,0.68); font-size: 10px;")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(about)

    def _toggle_row(self, text: str, kind: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(_label(text))
        row.addStretch(1)
        t = _toggle()
        row.addWidget(t, 0, Qt.AlignmentFlag.AlignRight)
        if kind == "grid":
            self.show_grid_toggle = t
            self.show_grid_toggle.toggled.connect(self.show_grid_changed.emit)
        elif kind == "crosshair":
            self.show_crosshair_toggle = t
            self.show_crosshair_toggle.toggled.connect(self.show_crosshair_changed.emit)
        elif kind == "autoscale":
            self.auto_scale_toggle = t
            self.auto_scale_toggle.toggled.connect(self.auto_scale_preview_changed.emit)
        else:
            self.camera_sound_toggle = t
            self.camera_sound_toggle.toggled.connect(self.camera_sound_changed.emit)
        return row

    def _value_row(self, name: str, val_text: str, with_auto: bool) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(_label(name))
        row.addStretch(1)
        val = _value(val_text, 600)
        row.addWidget(val)
        if with_auto:
            row.addSpacing(14)
            row.addWidget(_value("AUTO", 700))
            self._led_pct = val
        else:
            self._quality_pct = val
        return row

    def set_responsive_metrics(self, available_width: int, available_height: int) -> None:
        # Keep the panel compact and screenshot-like.
        width = max(290, min(360, int(available_width * 0.30)))
        height = max(470, min(680, int(available_height * 0.92)))
        self.setFixedWidth(width)
        self.setFixedHeight(height)

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

        self._quality_pct.setText(f"{jpeg_quality}%")
        self._led_pct.setText("50%")

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
