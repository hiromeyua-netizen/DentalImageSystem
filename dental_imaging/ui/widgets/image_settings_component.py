"""
Self-contained Image Settings UI + processing + hardware mapping.

Use this as the single integration point wherever live view or capture needs
image tuning. The main window (or other hosts) only wires camera I/O and
preview/capture pipelines; all slider semantics and post-processing live here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
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
    Floating panel: auto toggles for exposure / gain / white balance, plus seven sliders.

    Exposure & gain sliders apply to the camera when the matching Auto option is off.
    White Balance slider is software (tint) on top of the camera; Auto uses camera AWB.
    """

    settings_changed = pyqtSignal()
    panel_closed = pyqtSignal()
    #: ``True`` = camera auto mode enabled for that channel.
    auto_exposure_changed = pyqtSignal(bool)
    auto_gain_changed = pyqtSignal(bool)
    auto_white_balance_changed = pyqtSignal(bool)

    DEFAULT_PANEL_WIDTH = 380

    _SLIDER_ONLY_ROWS: Tuple[Tuple[str, str], ...] = (
        ("Contrast", "contrast"),
        ("Saturation", "saturation"),
        ("Warmth", "warmth"),
        ("Tint", "tint"),
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
                background-color: rgba(248, 248, 250, 242);
                border-radius: 10px;
                border: 1px solid rgba(200, 200, 210, 200);
            }
            QLabel#imageSettingsHeader {
                font-weight: 600;
                font-size: 14px;
            }
            QLabel#imageSettingsHint {
                color: #555;
                font-size: 11px;
            }
            QCheckBox {
                font-size: 12px;
            }
            """
        )

        self._sliders: Dict[str, QSlider] = {}
        self._labels: Dict[str, QLabel] = {}
        self._auto_exposure: QCheckBox
        self._auto_gain: QCheckBox
        self._auto_white_balance: QCheckBox

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Image Settings")
        title.setObjectName("imageSettingsHeader")
        header.addWidget(title)
        header.addStretch()

        reset_btn = QPushButton("Reset")
        reset_btn.setFlat(True)
        reset_btn.setToolTip("Set all sliders to 50% and turn Auto on for exposure, gain, and white balance")
        reset_btn.clicked.connect(self.reset_to_defaults)
        header.addWidget(reset_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setFlat(True)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._on_close_clicked)
        header.addWidget(close_btn)
        root.addLayout(header)

        hint = QLabel(
            "Auto: camera adjusts the image. Turn Auto off to control that row with the slider."
        )
        hint.setObjectName("imageSettingsHint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._auto_exposure = QCheckBox("Auto")
        self._auto_exposure.setToolTip(
            "Camera chooses exposure time. Turn off to set exposure with the slider below."
        )
        self._auto_exposure.setChecked(True)
        self._auto_exposure.toggled.connect(self._on_auto_exposure_toggled)
        self._add_slider_row_with_auto(
            root, "Exposure", "exposure", self._auto_exposure
        )

        self._auto_gain = QCheckBox("Auto")
        self._auto_gain.setToolTip(
            "Camera chooses gain. Turn off to set gain with the slider below."
        )
        self._auto_gain.setChecked(True)
        self._auto_gain.toggled.connect(self._on_auto_gain_toggled)
        self._add_slider_row_with_auto(root, "Gain", "gain", self._auto_gain)

        self._auto_white_balance = QCheckBox("Auto")
        self._auto_white_balance.setToolTip(
            "Camera white balance (continuous). Turn off for fixed WB; use the slider for fine color tuning."
        )
        self._auto_white_balance.setChecked(True)
        self._auto_white_balance.toggled.connect(self._on_auto_white_balance_toggled)
        self._add_slider_row_with_auto(
            root, "White Balance", "white_balance", self._auto_white_balance
        )

        for label_text, key in self._SLIDER_ONLY_ROWS:
            self._add_slider_row_only(root, label_text, key)

        self.setFixedWidth(self.DEFAULT_PANEL_WIDTH)

    def _add_slider_row_with_auto(
        self,
        root: QVBoxLayout,
        title: str,
        key: str,
        auto_cb: QCheckBox,
    ) -> None:
        block = QVBoxLayout()
        block.setSpacing(2)
        top = QHBoxLayout()
        name = QLabel(title)
        top.addWidget(name)
        top.addStretch()
        top.addWidget(auto_cb)
        block.addLayout(top)

        pct = QLabel("50%")
        pct.setMinimumWidth(40)
        pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_row = QHBoxLayout()
        label_row.addStretch()
        label_row.addWidget(pct)
        block.addLayout(label_row)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setTracking(True)
        slider.setEnabled(not auto_cb.isChecked())
        slider.valueChanged.connect(self._make_slider_handler(pct))
        self._sliders[key] = slider
        self._labels[key] = pct
        block.addWidget(slider)
        root.addLayout(block)

    def _add_slider_row_only(self, root: QVBoxLayout, title: str, key: str) -> None:
        block = QVBoxLayout()
        block.setSpacing(2)
        top = QHBoxLayout()
        top.addWidget(QLabel(title))
        top.addStretch()
        pct = QLabel("50%")
        pct.setMinimumWidth(40)
        pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(pct)
        block.addLayout(top)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setTracking(True)
        slider.valueChanged.connect(self._make_slider_handler(pct))
        self._sliders[key] = slider
        self._labels[key] = pct
        block.addWidget(slider)
        root.addLayout(block)

    @property
    def hardware_range(self) -> ImageSettingsHardwareRange:
        return self._hw

    def _on_auto_exposure_toggled(self, auto_on: bool) -> None:
        self._sliders["exposure"].setEnabled(not auto_on)
        self.auto_exposure_changed.emit(auto_on)

    def _on_auto_gain_toggled(self, auto_on: bool) -> None:
        self._sliders["gain"].setEnabled(not auto_on)
        self.auto_gain_changed.emit(auto_on)

    def _on_auto_white_balance_toggled(self, auto_on: bool) -> None:
        self.auto_white_balance_changed.emit(auto_on)

    def _make_slider_handler(self, pct_label: QLabel) -> Callable[[int], None]:
        def _on(v: int) -> None:
            pct_label.setText(f"{v}%")
            self.settings_changed.emit()

        return _on

    def _on_close_clicked(self) -> None:
        self.hide()
        self.panel_closed.emit()

    def is_auto_exposure(self) -> bool:
        return self._auto_exposure.isChecked()

    def is_auto_gain(self) -> bool:
        return self._auto_gain.isChecked()

    def is_auto_white_balance(self) -> bool:
        return self._auto_white_balance.isChecked()

    def set_auto_exposure(self, value: bool, *, block_signals: bool = False) -> None:
        if block_signals:
            self._auto_exposure.blockSignals(True)
        try:
            self._auto_exposure.setChecked(value)
            self._sliders["exposure"].setEnabled(not value)
        finally:
            if block_signals:
                self._auto_exposure.blockSignals(False)

    def set_auto_gain(self, value: bool, *, block_signals: bool = False) -> None:
        if block_signals:
            self._auto_gain.blockSignals(True)
        try:
            self._auto_gain.setChecked(value)
            self._sliders["gain"].setEnabled(not value)
        finally:
            if block_signals:
                self._auto_gain.blockSignals(False)

    def set_auto_white_balance(self, value: bool, *, block_signals: bool = False) -> None:
        if block_signals:
            self._auto_white_balance.blockSignals(True)
        try:
            self._auto_white_balance.setChecked(value)
        finally:
            if block_signals:
                self._auto_white_balance.blockSignals(False)

    def set_auto_white_balance_enabled(self, enabled: bool) -> None:
        self._auto_white_balance.setEnabled(enabled)

    def reset_to_defaults(self) -> None:
        """Sliders to 50%; Auto on for exposure, gain, and white balance."""
        for s in self._sliders.values():
            s.blockSignals(True)
        for cb in (self._auto_exposure, self._auto_gain, self._auto_white_balance):
            cb.blockSignals(True)
        try:
            for s in self._sliders.values():
                s.setValue(50)
            for lbl in self._labels.values():
                lbl.setText("50%")
            self._auto_exposure.setChecked(True)
            self._auto_gain.setChecked(True)
            self._auto_white_balance.setChecked(True)
            self._sliders["exposure"].setEnabled(False)
            self._sliders["gain"].setEnabled(False)
        finally:
            for cb in (self._auto_exposure, self._auto_gain, self._auto_white_balance):
                cb.blockSignals(False)
            for s in self._sliders.values():
                s.blockSignals(False)
        self.auto_exposure_changed.emit(True)
        self.auto_gain_changed.emit(True)
        self.auto_white_balance_changed.emit(True)
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
