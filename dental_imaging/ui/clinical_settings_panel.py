"""
Floating glass-style Settings panel (Occuscope / OccuView reference layout).
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# --- shared chrome tokens (aligned with clinical_shell) ---
GLASS_BG = "rgba(44, 48, 56, 0.88)"
GLASS_BORDER = "rgba(255, 255, 255, 0.14)"
SECTION_TITLE = "font-weight: 700; font-size: 12px; color: #ffffff; letter-spacing: 0.4px;"
BODY = "color: #e8e8e8; font-size: 12px;"
MUTED = "color: #a8a8a8; font-size: 10px;"


def _pill_pair(
    left_text: str,
    right_text: str,
) -> tuple[QPushButton, QPushButton, QButtonGroup]:
    """Two exclusive pill buttons (segmented control)."""
    group = QButtonGroup()
    group.setExclusive(True)
    a = QPushButton(left_text)
    b = QPushButton(right_text)
    for btn in (a, b):
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255,255,255,0.08);
                color: #e8e8e8;
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:checked {
                background-color: rgba(255,255,255,0.22);
                color: #ffffff;
                border-color: rgba(255,255,255,0.35);
            }
            QPushButton:hover:!checked { background-color: rgba(255,255,255,0.12); }
            """
        )
        group.addButton(btn)
    a.setChecked(True)
    return a, b, group


def _switch_row(label: str) -> tuple[QWidget, QCheckBox]:
    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 4, 0, 4)
    lab = QLabel(label)
    lab.setStyleSheet(BODY)
    cb = QCheckBox()
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setStyleSheet(
        """
        QCheckBox::indicator {
            width: 42px;
            height: 22px;
            border-radius: 11px;
            background-color: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.25);
        }
        QCheckBox::indicator:checked {
            background-color: rgba(130, 200, 140, 0.55);
            border-color: rgba(180, 230, 190, 0.5);
        }
        QCheckBox::indicator:unchecked:hover {
            background-color: rgba(255,255,255,0.24);
        }
        """
    )
    h.addWidget(lab, 1)
    h.addWidget(cb, 0, Qt.AlignmentFlag.AlignRight)
    return row, cb


def _section_title(text: str) -> QLabel:
    t = QLabel(text.upper())
    t.setObjectName("sectionTitle")
    t.setStyleSheet(SECTION_TITLE)
    return t


class ClinicalSettingsPanel(QFrame):
    """Translucent floating panel: Display, Capture, Storage, Camera service, About."""

    close_requested = pyqtSignal()
    show_grid_changed = pyqtSignal(bool)
    show_crosshair_changed = pyqtSignal(bool)
    auto_scale_preview_changed = pyqtSignal(bool)
    export_scope_changed = pyqtSignal(str)  # "preview" | "full"
    capture_format_changed = pyqtSignal(str)  # "jpg" | "png"
    jpeg_quality_changed = pyqtSignal(int)
    led_preset_changed = pyqtSignal(int)
    capture_mode_changed = pyqtSignal(str)  # "snapshot" | "burst"
    burst_delay_sec_changed = pyqtSignal(int)
    camera_sound_changed = pyqtSignal(bool)
    storage_target_changed = pyqtSignal(str)  # "system" | "sd"
    sd_card_requested = pyqtSignal()

    def __init__(self, app_name: str, app_version: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ClinicalSettingsPanelRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumWidth(380)
        self.setMaximumWidth(460)
        self.setStyleSheet(
            f"""
            QFrame#ClinicalSettingsPanelRoot {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 18px;
            }}
            QLabel#sectionTitle {{ {SECTION_TITLE} }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 16)
        outer.setSpacing(0)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #ffffff;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: #fff;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 16px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
            """
        )
        close_btn.clicked.connect(self._on_close)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(close_btn)
        outer.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        inner_l = QVBoxLayout(inner)
        inner_l.setSpacing(14)
        inner_l.setContentsMargins(0, 12, 4, 8)

        # --- Display ---
        inner_l.addWidget(_section_title("Display"))
        r1, self.show_grid_toggle = _switch_row("Show grid overlay")
        r2, self.show_crosshair_toggle = _switch_row("Show crosshair")
        r3, self.auto_scale_toggle = _switch_row("Auto scale preview")
        self.auto_scale_toggle.setChecked(True)
        inner_l.addWidget(r1)
        inner_l.addWidget(r2)
        inner_l.addWidget(r3)
        self.show_grid_toggle.toggled.connect(self.show_grid_changed.emit)
        self.show_crosshair_toggle.toggled.connect(self.show_crosshair_changed.emit)
        self.auto_scale_toggle.toggled.connect(self.auto_scale_preview_changed.emit)

        inner_l.addWidget(self._divider())

        # --- Capture ---
        inner_l.addWidget(_section_title("Capture"))
        cap_sub = QHBoxLayout()
        prev_lbl = QLabel("PREVIEW")
        prev_lbl.setStyleSheet(MUTED)
        exp_lbl = QLabel("Export all")
        exp_lbl.setStyleSheet(MUTED)
        cap_sub.addWidget(prev_lbl)
        cap_sub.addStretch(1)
        cap_sub.addWidget(exp_lbl)
        inner_l.addLayout(cap_sub)

        self._btn_preview_scope, self._btn_full_scope, self._scope_group = _pill_pair(
            "Preview", "Full resolution"
        )
        scope_row = QHBoxLayout()
        scope_row.addWidget(self._btn_preview_scope, 1)
        scope_row.addWidget(self._btn_full_scope, 1)
        inner_l.addLayout(scope_row)
        self._btn_preview_scope.toggled.connect(
            lambda c: c and self.export_scope_changed.emit("preview")
        )
        self._btn_full_scope.toggled.connect(
            lambda c: c and self.export_scope_changed.emit("full")
        )

        inner_l.addSpacing(6)
        fmt_lbl = QLabel("Image format")
        fmt_lbl.setStyleSheet(BODY)
        inner_l.addWidget(fmt_lbl)
        self._btn_jpg, self._btn_png, self._fmt_group = _pill_pair("JPG", "PNG")
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(self._btn_jpg, 1)
        fmt_row.addWidget(self._btn_png, 1)
        inner_l.addLayout(fmt_row)
        self._btn_jpg.toggled.connect(lambda c: c and self.capture_format_changed.emit("jpg"))
        self._btn_png.toggled.connect(lambda c: c and self.capture_format_changed.emit("png"))

        qual_row = QHBoxLayout()
        qual_lab = QLabel("Image quality")
        qual_lab.setStyleSheet(BODY)
        self._quality_pct = QLabel("94%")
        self._quality_pct.setStyleSheet("color: #fff; font-weight: 600; font-size: 12px;")
        self._quality_slider = QSlider(Qt.Orientation.Horizontal)
        self._quality_slider.setRange(60, 100)
        self._quality_slider.setValue(94)
        self._quality_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                height: 5px;
                background: rgba(255,255,255,0.15);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            """
        )
        qual_row.addWidget(qual_lab)
        qual_row.addStretch(1)
        qual_row.addWidget(self._quality_pct)
        inner_l.addLayout(qual_row)
        inner_l.addWidget(self._quality_slider)
        self._quality_slider.valueChanged.connect(self._on_quality_slider)

        inner_l.addSpacing(4)
        led_row = QHBoxLayout()
        led_lab = QLabel("LEDs preset")
        led_lab.setStyleSheet(BODY)
        self._led_pct = QLabel("50%")
        self._led_pct.setStyleSheet("color: #fff; font-weight: 600;")
        self._led_auto = QPushButton("AUTO")
        self._led_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self._led_auto.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.12);
                color: #fff;
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
            """
        )
        self._led_slider = QSlider(Qt.Orientation.Horizontal)
        self._led_slider.setRange(0, 100)
        self._led_slider.setValue(50)
        self._led_slider.valueChanged.connect(self._on_led_slider)
        led_row.addWidget(led_lab)
        led_row.addStretch(1)
        led_row.addWidget(self._led_pct)
        led_row.addWidget(self._led_auto)
        inner_l.addLayout(led_row)
        inner_l.addWidget(self._led_slider)
        self._led_auto.clicked.connect(self._on_led_auto)

        inner_l.addSpacing(8)
        mode_lbl = QLabel("Operation mode")
        mode_lbl.setStyleSheet(BODY)
        inner_l.addWidget(mode_lbl)
        self._btn_snapshot, self._btn_burst, self._mode_group = _pill_pair(
            "SNAPSHOT", "BURST"
        )
        mode_row = QHBoxLayout()
        mode_row.addWidget(self._btn_snapshot, 1)
        mode_row.addWidget(self._btn_burst, 1)
        inner_l.addLayout(mode_row)
        self._btn_snapshot.toggled.connect(
            lambda c: c and self.capture_mode_changed.emit("snapshot")
        )
        self._btn_burst.toggled.connect(lambda c: c and self.capture_mode_changed.emit("burst"))

        delay_lbl = QLabel("Delay (s)")
        delay_lbl.setStyleSheet(BODY)
        inner_l.addWidget(delay_lbl)
        delay_wrap = QWidget()
        dh = QHBoxLayout(delay_wrap)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.setSpacing(6)
        self._delay_group = QButtonGroup()
        self._delay_group.setExclusive(True)
        self._delay_buttons: dict[int, QPushButton] = {}
        for sec in (2, 5, 10, 15, 30, 60):
            b = QPushButton(str(sec))
            b.setCheckable(True)
            b.setFixedSize(36, 36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255,255,255,0.08);
                    color: #ddd;
                    border: 1px solid rgba(255,255,255,0.15);
                    border-radius: 18px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: #ffffff;
                    color: #222;
                    border-color: #fff;
                }
                QPushButton:hover:!checked { background: rgba(255,255,255,0.14); }
                """
            )
            self._delay_group.addButton(b)
            self._delay_buttons[sec] = b
            dh.addWidget(b)
            b.toggled.connect(lambda c, s=sec: c and self.burst_delay_sec_changed.emit(s))
        self._delay_buttons[10].setChecked(True)
        dh.addStretch(1)
        inner_l.addWidget(delay_wrap)

        r_sound, self.camera_sound_toggle = _switch_row("Camera sound")
        inner_l.addWidget(r_sound)
        self.camera_sound_toggle.toggled.connect(self.camera_sound_changed.emit)

        inner_l.addWidget(self._divider())

        # --- Storage ---
        inner_l.addWidget(_section_title("Storage"))
        self._btn_system, self._btn_sd, self._storage_group = _pill_pair(
            "SYSTEM", "SD CARD"
        )
        stor_row = QHBoxLayout()
        stor_row.addWidget(self._btn_system, 1)
        stor_row.addWidget(self._btn_sd, 1)
        inner_l.addLayout(stor_row)
        self._btn_system.toggled.connect(
            lambda c: c and self.storage_target_changed.emit("system")
        )
        self._btn_sd.toggled.connect(self._on_sd_toggled)

        inner_l.addWidget(self._divider())

        # --- Camera (service) ---
        inner_l.addWidget(_section_title("Camera"))
        cam_note = QLabel("Frame rate, gamma, and transport")
        cam_note.setStyleSheet(MUTED)
        inner_l.addWidget(cam_note)

        fr_row = QHBoxLayout()
        fr_lab = QLabel("Frame rate")
        fr_lab.setStyleSheet(BODY)
        self.frame_rate_spinbox = QDoubleSpinBox()
        self.frame_rate_spinbox.setRange(1.0, 60.0)
        self.frame_rate_spinbox.setSuffix(" fps")
        self.frame_rate_spinbox.setDecimals(1)
        self.frame_rate_spinbox.setSingleStep(1.0)
        fr_row.addWidget(fr_lab)
        fr_row.addWidget(self.frame_rate_spinbox, 1)
        inner_l.addLayout(fr_row)

        gamma_row = QHBoxLayout()
        g_lab = QLabel("Gamma")
        g_lab.setStyleSheet(BODY)
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(50, 300)
        self.gamma_slider.setValue(100)
        self.gamma_spinbox = QDoubleSpinBox()
        self.gamma_spinbox.setRange(0.5, 3.0)
        self.gamma_spinbox.setSingleStep(0.1)
        self.gamma_spinbox.setDecimals(2)
        gamma_row.addWidget(g_lab)
        gamma_row.addWidget(self.gamma_slider, 1)
        gamma_row.addWidget(self.gamma_spinbox)
        inner_l.addLayout(gamma_row)
        self.gamma_slider.valueChanged.connect(self._sync_gamma_spin_from_slider)
        self.gamma_spinbox.valueChanged.connect(self._sync_gamma_slider_from_spin)

        svc_grid = QGridLayout()
        self.start_preview_btn = QPushButton("Start preview")
        self.stop_preview_btn = QPushButton("Stop preview")
        self.diagnose_btn = QPushButton("Diagnose blur")
        self.reconnect_btn = QPushButton("Reconnect")
        for b in (
            self.start_preview_btn,
            self.stop_preview_btn,
            self.diagnose_btn,
            self.reconnect_btn,
        ):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255,255,255,0.1);
                    color: #eee;
                    border: 1px solid rgba(255,255,255,0.18);
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 11px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.16); }
                """
            )
        svc_grid.addWidget(self.start_preview_btn, 0, 0)
        svc_grid.addWidget(self.stop_preview_btn, 0, 1)
        svc_grid.addWidget(self.diagnose_btn, 1, 0)
        svc_grid.addWidget(self.reconnect_btn, 1, 1)
        inner_l.addLayout(svc_grid)

        inner_l.addSpacing(10)
        about = QLabel(f"{app_name} {app_version}\n© 2026")
        about.setStyleSheet(MUTED + " font-size: 10px;")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_l.addWidget(about)

        inner_l.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(255,255,255,0.1); border: none; max-height: 1px;")
        return line

    def _on_close(self) -> None:
        self.close_requested.emit()

    def _on_quality_slider(self, v: int) -> None:
        self._quality_pct.setText(f"{v}%")
        self.jpeg_quality_changed.emit(v)

    def _on_led_slider(self, v: int) -> None:
        self._led_pct.setText(f"{v}%")
        self.led_preset_changed.emit(v)

    def _on_led_auto(self) -> None:
        self._led_slider.blockSignals(True)
        self._led_slider.setValue(50)
        self._led_slider.blockSignals(False)
        self._led_pct.setText("50%")
        self.led_preset_changed.emit(50)

    def _on_sd_toggled(self, checked: bool) -> None:
        if checked:
            self.storage_target_changed.emit("sd")
            self.sd_card_requested.emit()

    def _sync_gamma_spin_from_slider(self, value: int) -> None:
        self.gamma_spinbox.blockSignals(True)
        self.gamma_spinbox.setValue(value / 100.0)
        self.gamma_spinbox.blockSignals(False)

    def _sync_gamma_slider_from_spin(self, value: float) -> None:
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(int(value * 100))
        self.gamma_slider.blockSignals(False)

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
        frame_rate: float,
        gamma_slider_value: int,
        gamma_spin_value: float,
    ) -> None:
        """Apply state without emitting signals (blockSignals)."""
        self.show_grid_toggle.blockSignals(True)
        self.show_crosshair_toggle.blockSignals(True)
        self.auto_scale_toggle.blockSignals(True)
        self.show_grid_toggle.setChecked(show_grid)
        self.show_crosshair_toggle.setChecked(show_crosshair)
        self.auto_scale_toggle.setChecked(auto_scale)
        self.show_grid_toggle.blockSignals(False)
        self.show_crosshair_toggle.blockSignals(False)
        self.auto_scale_toggle.blockSignals(False)

        self._btn_preview_scope.blockSignals(True)
        self._btn_full_scope.blockSignals(True)
        if export_full_resolution:
            self._btn_full_scope.setChecked(True)
        else:
            self._btn_preview_scope.setChecked(True)
        self._btn_preview_scope.blockSignals(False)
        self._btn_full_scope.blockSignals(False)

        fmt = (image_format or "png").lower()
        if fmt in ("jpeg",):
            fmt = "jpg"
        self._btn_jpg.blockSignals(True)
        self._btn_png.blockSignals(True)
        if fmt == "jpg":
            self._btn_jpg.setChecked(True)
        else:
            self._btn_png.setChecked(True)
        self._btn_jpg.blockSignals(False)
        self._btn_png.blockSignals(False)

        self._quality_slider.blockSignals(True)
        self._quality_slider.setValue(jpeg_quality)
        self._quality_slider.blockSignals(False)
        self._quality_pct.setText(f"{jpeg_quality}%")

        self._btn_snapshot.blockSignals(True)
        self._btn_burst.blockSignals(True)
        if capture_mode_burst:
            self._btn_burst.setChecked(True)
        else:
            self._btn_snapshot.setChecked(True)
        self._btn_snapshot.blockSignals(False)
        self._btn_burst.blockSignals(False)

        for sec, btn in self._delay_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(sec == burst_delay_sec)
            btn.blockSignals(False)

        self.camera_sound_toggle.blockSignals(True)
        self.camera_sound_toggle.setChecked(camera_sound)
        self.camera_sound_toggle.blockSignals(False)

        self._btn_system.blockSignals(True)
        self._btn_sd.blockSignals(True)
        if storage_sd_selected:
            self._btn_sd.setChecked(True)
        else:
            self._btn_system.setChecked(True)
        self._btn_system.blockSignals(False)
        self._btn_sd.blockSignals(False)

        self.frame_rate_spinbox.blockSignals(True)
        self.frame_rate_spinbox.setValue(frame_rate)
        self.frame_rate_spinbox.blockSignals(False)

        self.gamma_slider.blockSignals(True)
        self.gamma_spinbox.blockSignals(True)
        self.gamma_slider.setValue(gamma_slider_value)
        self.gamma_spinbox.setValue(gamma_spin_value)
        self.gamma_slider.blockSignals(False)
        self.gamma_spinbox.blockSignals(False)
