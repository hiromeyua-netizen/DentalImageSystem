"""
Self-contained Image Settings UI + processing + hardware mapping.

Reset restores camera automatic exposure, gain, and white balance (same effect as
the former Auto checkboxes). Moving the exposure or gain slider switches that
parameter to manual until the next Reset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from dental_imaging.image_processing.color_adjustments import (
    ImageSettingsPercent,
    apply_software_image_adjustments,
)


@dataclass(frozen=True)
class ImageSettingsHardwareRange:
    """Maps 0–100% exposure/gain sliders to camera units (override per camera if needed)."""

    exposure_us_min: int = 1000
    exposure_us_max: int = 200_000
    gain_max: float = 20.0

    def __post_init__(self) -> None:
        if self.exposure_us_max <= self.exposure_us_min:
            raise ValueError("exposure_us_max must be greater than exposure_us_min")
        if self.gain_max <= 0:
            raise ValueError("gain_max must be positive")


class ImageSettingsComponent(QFrame):
    """
    Seven sliders for image tuning. Reset sets neutral sliders and signals the host
    to restore camera auto exposure, gain, and white balance.
    """

    settings_changed = pyqtSignal()
    panel_closed = pyqtSignal()
    #: Emitted after Reset (sliders at 50%); host should set camera AE/AGC/AWB on.
    defaults_restored = pyqtSignal()
    #: User moved the exposure slider (not a programmatic sync).
    exposure_slider_user_changed = pyqtSignal()
    #: User moved the gain slider (not a programmatic sync).
    gain_slider_user_changed = pyqtSignal()

    DEFAULT_PANEL_WIDTH = 340

    _ROW_META: Tuple[Tuple[str, str, str], ...] = (
        ("Exposure", "exposure", "Adjust brightness timing. Reset restores automatic exposure on the camera."),
        ("Gain", "gain", "Adjust analog gain. Reset restores automatic gain on the camera."),
        (
            "White Balance",
            "white_balance",
            "Software color balance. Reset restores automatic white balance on the camera.",
        ),
        ("Contrast", "contrast", ""),
        ("Saturation", "saturation", ""),
        ("Warmth", "warmth", ""),
        ("Tint", "tint", ""),
    )

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        hardware_range: Optional[ImageSettingsHardwareRange] = None,
    ) -> None:
        super().__init__(parent)
        self._hw = hardware_range or ImageSettingsHardwareRange()

        self.setObjectName("ImageSettingsComponent")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#ImageSettingsComponent {
                background-color: rgba(170, 136, 136, 0.48);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.20);
            }
            QLabel#imageSettingsHeader {
                font-weight: 700;
                font-size: 16px;
                color: rgba(255, 255, 255, 0.95);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.92);
                font-size: 12px;
            }
            QLabel#sliderPctBubble {
                background-color: rgba(120, 125, 132, 0.95);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.95);
                font-size: 9px;
                font-weight: 600;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                qproperty-alignment: AlignCenter;
            }
            QPushButton {
                color: rgba(255, 255, 255, 0.95);
                border: none;
                background: transparent;
                font-size: 13px;
                font-weight: 600;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(255,255,255,0.90);
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(120, 128, 138, 0.95);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                background: rgba(122,130,140,1.0);
                border: 1px solid rgba(255,255,255,0.45);
            }
            """
        )

        self._sliders: Dict[str, QSlider] = {}
        self._labels: Dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Image Settings")
        title.setObjectName("imageSettingsHeader")
        header.addWidget(title)
        header.addStretch()

        reset_btn = QPushButton("Reset")
        reset_btn.setFlat(True)
        reset_btn.setToolTip(
            "Neutral sliders and automatic exposure, gain, and white balance on the camera"
        )
        reset_btn.clicked.connect(self.reset_to_defaults)
        header.addWidget(reset_btn)

        close_btn = QPushButton("X")
        close_btn.setFixedWidth(28)
        close_btn.setFlat(True)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._on_close_clicked)
        header.addWidget(close_btn)
        root.addLayout(header)

        for label_text, key, tip in self._ROW_META:
            self._add_slider_row(root, label_text, key, tip or None)

        self.setFixedWidth(self.DEFAULT_PANEL_WIDTH)

    def _add_slider_row(
        self,
        root: QVBoxLayout,
        title: str,
        key: str,
        tooltip: Optional[str],
    ) -> None:
        block = QVBoxLayout()
        block.setSpacing(4)
        top = QHBoxLayout()
        name = QLabel(title)
        if tooltip:
            name.setToolTip(tooltip)
        top.addWidget(name)
        top.addStretch()
        pct = QLabel("50%")
        pct.setObjectName("sliderPctBubble")
        top.addWidget(pct)
        block.addLayout(top)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setTracking(True)
        if tooltip:
            slider.setToolTip(tooltip)
        slider.valueChanged.connect(self._make_slider_handler(key, pct))
        self._sliders[key] = slider
        self._labels[key] = pct
        block.addWidget(slider)
        root.addLayout(block)

    @property
    def hardware_range(self) -> ImageSettingsHardwareRange:
        return self._hw

    def _make_slider_handler(self, key: str, pct_label: QLabel) -> Callable[[int], None]:
        def _on(v: int) -> None:
            pct_label.setText(f"{v}%")
            if key == "exposure":
                self.exposure_slider_user_changed.emit()
            elif key == "gain":
                self.gain_slider_user_changed.emit()
            self.settings_changed.emit()

        return _on

    def _on_close_clicked(self) -> None:
        self.hide()
        self.panel_closed.emit()

    def reset_to_defaults(self) -> None:
        """All sliders to 50%; notify host to enable camera AE, AGC, and AWB."""
        for s in self._sliders.values():
            s.blockSignals(True)
        try:
            for s in self._sliders.values():
                s.setValue(50)
            for lbl in self._labels.values():
                lbl.setText("50%")
        finally:
            for s in self._sliders.values():
                s.blockSignals(False)
        self.defaults_restored.emit()
        self.settings_changed.emit()

    def get_values(self) -> ImageSettingsPercent:
        return ImageSettingsPercent(
            exposure=self._sliders["exposure"].value(),
            gain=self._sliders["gain"].value(),
            white_balance=self._sliders["white_balance"].value(),
            contrast=self._sliders["contrast"].value(),
            saturation=self._sliders["saturation"].value(),
            warmth=self._sliders["warmth"].value(),
            tint=self._sliders["tint"].value(),
        )

    def set_values(self, values: ImageSettingsPercent, *, block_signals: bool = True) -> None:
        """Apply all slider values from a preset snapshot."""
        mapping = {
            "exposure": int(values.exposure),
            "gain": int(values.gain),
            "white_balance": int(values.white_balance),
            "contrast": int(values.contrast),
            "saturation": int(values.saturation),
            "warmth": int(values.warmth),
            "tint": int(values.tint),
        }
        for key, slider in self._sliders.items():
            if block_signals:
                slider.blockSignals(True)
            try:
                v = max(0, min(100, mapping[key]))
                slider.setValue(v)
                self._labels[key].setText(f"{v}%")
            finally:
                if block_signals:
                    slider.blockSignals(False)
        self.settings_changed.emit()

    def apply_postprocess(self, bgr: np.ndarray) -> np.ndarray:
        return apply_software_image_adjustments(bgr, self.get_values())

    def exposure_time_microseconds(self) -> int:
        pct = max(0, min(100, self._sliders["exposure"].value()))
        span = self._hw.exposure_us_max - self._hw.exposure_us_min
        return int(self._hw.exposure_us_min + span * pct / 100.0)

    def analog_gain(self) -> float:
        pct = max(0, min(100, self._sliders["gain"].value()))
        return self._hw.gain_max * pct / 100.0

    def exposure_percent_from_microseconds(self, us: int) -> int:
        span = self._hw.exposure_us_max - self._hw.exposure_us_min
        if span <= 0:
            return 50
        u = max(self._hw.exposure_us_min, min(self._hw.exposure_us_max, int(us)))
        return int(round((u - self._hw.exposure_us_min) / span * 100.0))

    def gain_percent_from_analog(self, gain: float) -> int:
        g = max(0.0, min(self._hw.gain_max, float(gain)))
        return int(round(g / self._hw.gain_max * 100.0))

    def set_exposure_percent(self, pct: int, *, block_signals: bool = False) -> None:
        v = max(0, min(100, int(pct)))
        s = self._sliders["exposure"]
        if block_signals:
            s.blockSignals(True)
        try:
            s.setValue(v)
            self._labels["exposure"].setText(f"{v}%")
        finally:
            if block_signals:
                s.blockSignals(False)

    def set_gain_percent(self, pct: int, *, block_signals: bool = False) -> None:
        v = max(0, min(100, int(pct)))
        s = self._sliders["gain"]
        if block_signals:
            s.blockSignals(True)
        try:
            s.setValue(v)
            self._labels["gain"].setText(f"{v}%")
        finally:
            if block_signals:
                s.blockSignals(False)

    def set_panel_visible(self, visible: bool) -> None:
        self.setVisible(visible)

    def wire_toggle_button(self, button: QAbstractButton) -> None:
        if not button.isCheckable():
            button.setCheckable(True)

        def on_toggled(checked: bool) -> None:
            self.setVisible(checked)

        button.toggled.connect(on_toggled)
        self.panel_closed.connect(lambda: button.setChecked(False))
