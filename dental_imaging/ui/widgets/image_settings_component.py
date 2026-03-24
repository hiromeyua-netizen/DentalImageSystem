"""
Self-contained Image Settings UI + processing + hardware mapping.

Use this as the single integration point wherever live view or capture needs
image tuning. The main window (or other hosts) only wires camera I/O and
preview/capture pipelines; all slider semantics and post-processing live here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

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
    Floating panel: Exposure, Gain, White Balance, Contrast, Saturation, Warmth, Tint.

    Responsibilities:
    - Render and persist slider state (0–100, 50 = neutral).
    - Apply software adjustments to BGR frames (:meth:`apply_postprocess`).
    - Expose :meth:`exposure_time_microseconds` / :meth:`analog_gain` for host-driven
      hardware updates when auto modes are off.
    """

    #: Emitted after any slider change or reset (host reads :meth:`get_values` or hardware helpers).
    settings_changed = pyqtSignal()
    panel_closed = pyqtSignal()

    SLIDER_ROWS: tuple[tuple[str, str], ...] = (
        ("Exposure", "exposure"),
        ("Gain", "gain"),
        ("White Balance", "white_balance"),
        ("Contrast", "contrast"),
        ("Saturation", "saturation"),
        ("Warmth", "warmth"),
        ("Tint", "tint"),
    )

    DEFAULT_PANEL_WIDTH = 360

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
            """
        )

        self._sliders: Dict[str, QSlider] = {}
        self._labels: Dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Image Settings")
        title.setObjectName("imageSettingsHeader")
        header.addWidget(title)
        header.addStretch()

        reset_btn = QPushButton("Reset")
        reset_btn.setFlat(True)
        reset_btn.clicked.connect(self.reset_to_defaults)
        header.addWidget(reset_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setFlat(True)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._on_close_clicked)
        header.addWidget(close_btn)
        root.addLayout(header)

        for label_text, key in self.SLIDER_ROWS:
            row = QVBoxLayout()
            row.setSpacing(2)
            top = QHBoxLayout()
            name = QLabel(label_text)
            top.addWidget(name)
            top.addStretch()
            pct = QLabel("50%")
            pct.setMinimumWidth(40)
            pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            top.addWidget(pct)
            row.addLayout(top)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            slider.setTracking(True)
            slider.valueChanged.connect(self._make_slider_handler(pct))
            self._sliders[key] = slider
            self._labels[key] = pct
            row.addWidget(slider)
            root.addLayout(row)

        self.setFixedWidth(self.DEFAULT_PANEL_WIDTH)

    @property
    def hardware_range(self) -> ImageSettingsHardwareRange:
        return self._hw

    def _make_slider_handler(self, pct_label: QLabel) -> Callable[[int], None]:
        def _on(v: int) -> None:
            pct_label.setText(f"{v}%")
            self.settings_changed.emit()

        return _on

    def _on_close_clicked(self) -> None:
        self.hide()
        self.panel_closed.emit()

    def reset_to_defaults(self) -> None:
        """Set all sliders to 50% and notify listeners."""
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
        """Apply software color adjustments (WB, contrast, saturation, warmth, tint)."""
        return apply_software_image_adjustments(bgr, self.get_values())

    def exposure_time_microseconds(self) -> int:
        """Current exposure slider as microseconds (for manual camera mode)."""
        pct = max(0, min(100, self._sliders["exposure"].value()))
        span = self._hw.exposure_us_max - self._hw.exposure_us_min
        return int(self._hw.exposure_us_min + span * pct / 100.0)

    def analog_gain(self) -> float:
        """Current gain slider as camera analog gain (for manual camera mode)."""
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

    def set_exposure_slider_enabled(self, enabled: bool) -> None:
        self._sliders["exposure"].setEnabled(enabled)

    def set_gain_slider_enabled(self, enabled: bool) -> None:
        self._sliders["gain"].setEnabled(enabled)

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
        """
        Keep panel visibility in sync with a checkable toolbar button.

        The button should be ``setCheckable(True)``. Panel hide (✕) unchecks the button.
        """
        if not button.isCheckable():
            button.setCheckable(True)

        def on_toggled(checked: bool) -> None:
            self.setVisible(checked)

        button.toggled.connect(on_toggled)
        self.panel_closed.connect(lambda: button.setChecked(False))
