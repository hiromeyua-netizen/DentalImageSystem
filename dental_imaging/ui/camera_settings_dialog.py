"""Modal dialog for camera tuning and service actions (keeps kiosk chrome minimal)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class CameraSettingsDialog(QDialog):
    """Frame rate, gamma, preview transport, diagnostics (invoked from Settings on the rail)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Camera & preview")
        self.setModal(True)
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)

        form = QFormLayout()
        self.frame_rate_spinbox = QDoubleSpinBox()
        self.frame_rate_spinbox.setRange(1.0, 60.0)
        self.frame_rate_spinbox.setSuffix(" fps")
        self.frame_rate_spinbox.setSingleStep(1.0)
        self.frame_rate_spinbox.setDecimals(1)
        form.addRow("Frame rate:", self.frame_rate_spinbox)

        gamma_row = QHBoxLayout()
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(50, 300)
        self.gamma_slider.setValue(100)
        self.gamma_spinbox = QDoubleSpinBox()
        self.gamma_spinbox.setRange(0.5, 3.0)
        self.gamma_spinbox.setSingleStep(0.1)
        self.gamma_spinbox.setDecimals(2)
        gamma_row.addWidget(self.gamma_slider, 1)
        gamma_row.addWidget(self.gamma_spinbox)
        form.addRow("Gamma:", gamma_row)

        root.addLayout(form)

        btn_grid = QGridLayout()
        self.start_preview_btn = QPushButton("Start preview")
        self.stop_preview_btn = QPushButton("Stop preview")
        self.diagnose_btn = QPushButton("Diagnose blur")
        self.reconnect_btn = QPushButton("Reconnect camera")
        btn_grid.addWidget(self.start_preview_btn, 0, 0)
        btn_grid.addWidget(self.stop_preview_btn, 0, 1)
        btn_grid.addWidget(self.diagnose_btn, 1, 0)
        btn_grid.addWidget(self.reconnect_btn, 1, 1)
        root.addLayout(btn_grid)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._buttons.rejected.connect(self.reject)
        close_btn = self._buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.clicked.connect(self.reject)
        root.addWidget(self._buttons)

        self.gamma_slider.valueChanged.connect(self._on_gamma_slider)
        self.gamma_spinbox.valueChanged.connect(self._on_gamma_spinbox)

    def _on_gamma_slider(self, value: int) -> None:
        self.gamma_spinbox.blockSignals(True)
        self.gamma_spinbox.setValue(value / 100.0)
        self.gamma_spinbox.blockSignals(False)

    def _on_gamma_spinbox(self, value: float) -> None:
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(int(value * 100))
        self.gamma_slider.blockSignals(False)
