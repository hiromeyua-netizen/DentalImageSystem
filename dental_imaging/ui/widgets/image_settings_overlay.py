"""
Floating "Image Settings" panel: Exposure, Gain, White Balance, Contrast,
Saturation, Warmth, Tint (0–100%, 50 = neutral).
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from dental_imaging.image_processing.color_adjustments import ImageSettingsPercent


class ImageSettingsOverlay(QFrame):
    """
    Semi-opaque panel with seven labeled percentage sliders and Reset / Close.
    """

    settings_changed = pyqtSignal()
    panel_closed = pyqtSignal()

    ROWS = (
        ("Exposure", "exposure"),
        ("Gain", "gain"),
        ("White Balance", "white_balance"),
        ("Contrast", "contrast"),
        ("Saturation", "saturation"),
        ("Warmth", "warmth"),
        ("Tint", "tint"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ImageSettingsOverlay")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#ImageSettingsOverlay {
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
        reset_btn.clicked.connect(self._on_reset)
        header.addWidget(reset_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setFlat(True)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._on_close_clicked)
        header.addWidget(close_btn)
        root.addLayout(header)

        for label_text, key in self.ROWS:
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
            slider.valueChanged.connect(self._make_slider_handler(key, pct))
            self._sliders[key] = slider
            self._labels[key] = pct
            row.addWidget(slider)
            root.addLayout(row)

        self.setFixedWidth(360)

    def _on_close_clicked(self) -> None:
        self.hide()
        self.panel_closed.emit()

    def _make_slider_handler(self, key: str, pct_label: QLabel) -> Callable[[int], None]:
        def _on(v: int) -> None:
            pct_label.setText(f"{v}%")
            self.settings_changed.emit()

        return _on

    def _on_reset(self) -> None:
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

    def set_exposure_slider_enabled(self, enabled: bool) -> None:
        self._sliders["exposure"].setEnabled(enabled)

    def set_gain_slider_enabled(self, enabled: bool) -> None:
        self._sliders["gain"].setEnabled(enabled)

    def set_exposure_percent(self, pct: int, *, block_signals: bool = False) -> None:
        v = max(0, min(100, int(pct)))
        if block_signals:
            self._sliders["exposure"].blockSignals(True)
        try:
            self._sliders["exposure"].setValue(v)
            self._labels["exposure"].setText(f"{v}%")
        finally:
            if block_signals:
                self._sliders["exposure"].blockSignals(False)

    def set_gain_percent(self, pct: int, *, block_signals: bool = False) -> None:
        v = max(0, min(100, int(pct)))
        if block_signals:
            self._sliders["gain"].blockSignals(True)
        try:
            self._sliders["gain"].setValue(v)
            self._labels["gain"].setText(f"{v}%")
        finally:
            if block_signals:
                self._sliders["gain"].blockSignals(False)
