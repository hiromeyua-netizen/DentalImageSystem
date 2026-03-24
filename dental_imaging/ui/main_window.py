"""
Main application window.
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStatusBar,
    QMessageBox,
    QLabel,
    QSlider,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from dental_imaging.ui.widgets.preview_widget import PreviewWidget
from dental_imaging.hardware.camera import BaslerCamera
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.exceptions import (
    CameraNotFoundError,
    CameraConnectionError,
    CameraConfigurationError,
    CameraGrabError,
)
from dental_imaging.settings import (
    ApplicationSettings,
    load_app_settings,
    resolve_default_config_path,
    resolve_storage_directory,
)
from dental_imaging.storage.snapshot_writer import SnapshotWriter
from dental_imaging.hardware.camera.camera_settings_helper import (
    get_camera_settings,
    print_camera_settings,
)
from dental_imaging.hardware.camera.focus_helper import diagnose_blur_issues


class MainWindow(QMainWindow):
    """
    Main application window for dental imaging system.
    """
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        app_settings: Optional[ApplicationSettings] = None,
    ):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
            app_settings: Loaded application config; if omitted, loads from the default path.
        """
        super().__init__(parent)

        self._app_settings = app_settings or load_app_settings(
            resolve_default_config_path()
        )
        storage_dir = resolve_storage_directory(self._app_settings)
        self._snapshot_writer = SnapshotWriter(
            storage_dir,
            self._app_settings.storage.default_format,
        )
        self._preview_width = self._app_settings.preview.width
        self._preview_height = self._app_settings.preview.height
        
        self.camera: Optional[BaslerCamera] = None
        self.camera_config: Optional[CameraConfig] = None
        self.preview_timer: Optional[QTimer] = None
        
        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(
            f"{self._app_settings.application.name} — Camera"
        )
        self.setMinimumSize(1280, 720)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Preview widget
        self.preview_widget = PreviewWidget()
        main_layout.addWidget(self.preview_widget, stretch=1)
        
        # Camera settings controls
        settings_group = QGroupBox("Camera Settings")
        settings_layout = QGridLayout()
        settings_group.setLayout(settings_layout)
        
        # Exposure controls
        settings_layout.addWidget(QLabel("Exposure:"), 0, 0)
        
        self.exposure_auto_checkbox = QCheckBox("Auto")
        self.exposure_auto_checkbox.setChecked(True)
        self.exposure_auto_checkbox.stateChanged.connect(self.on_exposure_auto_changed)
        settings_layout.addWidget(self.exposure_auto_checkbox, 0, 1)
        
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setRange(1000, 200000)  # 1ms to 200ms
        self.exposure_slider.setValue(50000)  # 50ms default
        self.exposure_slider.setEnabled(False)
        self.exposure_slider.valueChanged.connect(self.on_exposure_changed)
        settings_layout.addWidget(self.exposure_slider, 0, 2)
        
        self.exposure_spinbox = QSpinBox()
        self.exposure_spinbox.setRange(1000, 200000)
        self.exposure_spinbox.setValue(50000)
        self.exposure_spinbox.setSuffix(" μs")
        self.exposure_spinbox.setEnabled(False)
        self.exposure_spinbox.valueChanged.connect(self.on_exposure_spinbox_changed)
        settings_layout.addWidget(self.exposure_spinbox, 0, 3)
        
        # Gain controls
        settings_layout.addWidget(QLabel("Gain:"), 1, 0)
        
        self.gain_auto_checkbox = QCheckBox("Auto")
        self.gain_auto_checkbox.setChecked(True)
        self.gain_auto_checkbox.stateChanged.connect(self.on_gain_auto_changed)
        settings_layout.addWidget(self.gain_auto_checkbox, 1, 1)
        
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 200)  # 0.0 to 20.0 (multiply by 0.1)
        self.gain_slider.setValue(50)  # 5.0 default
        self.gain_slider.setEnabled(False)
        self.gain_slider.valueChanged.connect(self.on_gain_changed)
        settings_layout.addWidget(self.gain_slider, 1, 2)
        
        self.gain_spinbox = QDoubleSpinBox()
        self.gain_spinbox.setRange(0.0, 20.0)
        self.gain_spinbox.setValue(5.0)
        self.gain_spinbox.setSingleStep(0.1)
        self.gain_spinbox.setDecimals(1)
        self.gain_spinbox.setEnabled(False)
        self.gain_spinbox.valueChanged.connect(self.on_gain_spinbox_changed)
        settings_layout.addWidget(self.gain_spinbox, 1, 3)
        
        # White balance control
        settings_layout.addWidget(QLabel("White Balance:"), 2, 0)
        
        self.white_balance_auto_checkbox = QCheckBox("Auto")
        self.white_balance_auto_checkbox.setChecked(True)
        self.white_balance_auto_checkbox.stateChanged.connect(self.on_white_balance_auto_changed)
        settings_layout.addWidget(self.white_balance_auto_checkbox, 2, 1)
        
        # Frame rate control
        settings_layout.addWidget(QLabel("Frame Rate:"), 3, 0)
        
        self.frame_rate_spinbox = QDoubleSpinBox()
        self.frame_rate_spinbox.setRange(1.0, 60.0)
        self.frame_rate_spinbox.setValue(30.0)
        self.frame_rate_spinbox.setSuffix(" fps")
        self.frame_rate_spinbox.setSingleStep(1.0)
        self.frame_rate_spinbox.setDecimals(1)
        self.frame_rate_spinbox.valueChanged.connect(self.on_frame_rate_changed)
        settings_layout.addWidget(self.frame_rate_spinbox, 3, 1, 1, 3)
        
        # Gamma control (if supported)
        settings_layout.addWidget(QLabel("Gamma:"), 4, 0)
        
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(50, 300)  # 0.5 to 3.0 (multiply by 0.01)
        self.gamma_slider.setValue(100)  # 1.0 default
        self.gamma_slider.valueChanged.connect(self.on_gamma_changed)
        settings_layout.addWidget(self.gamma_slider, 4, 2)
        
        self.gamma_spinbox = QDoubleSpinBox()
        self.gamma_spinbox.setRange(0.5, 3.0)
        self.gamma_spinbox.setValue(1.0)
        self.gamma_spinbox.setSingleStep(0.1)
        self.gamma_spinbox.setDecimals(2)
        self.gamma_spinbox.valueChanged.connect(self.on_gamma_spinbox_changed)
        settings_layout.addWidget(self.gamma_spinbox, 4, 3)
        
        main_layout.addWidget(settings_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_button = QPushButton("Start Preview")
        self.start_button.clicked.connect(self.start_preview)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Preview")
        self.stop_button.clicked.connect(self.stop_preview)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setEnabled(False)
        button_layout.addWidget(self.capture_button)
        
        self.diagnose_button = QPushButton("Diagnose Blur")
        self.diagnose_button.clicked.connect(self.diagnose_blur)
        button_layout.addWidget(self.diagnose_button)

        self.reconnect_button = QPushButton("Reconnect Camera")
        self.reconnect_button.clicked.connect(self.reconnect_camera)
        self.reconnect_button.setEnabled(False)
        button_layout.addWidget(self.reconnect_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Flag to prevent recursive updates
        self._updating_settings = False
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def _setup_timers(self) -> None:
        """Set up timers for preview updates."""
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        fps = max(1.0, float(self._app_settings.preview.fps))
        self.preview_timer.setInterval(max(1, int(round(1000.0 / fps))))
        
    def initialize_camera(self, config: CameraConfig) -> bool:
        """
        Initialize camera with configuration.
        
        Args:
            config: Camera configuration
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.statusBar().showMessage("Connecting to camera...")
            
            # Create and connect camera
            self.camera = BaslerCamera()
            self.camera.connect()
            
            # Configure camera
            self.camera.configure(config)
            self.camera_config = config
            
            # Update UI controls with current settings
            self._update_settings_ui()
            
            # Print camera settings for diagnostics
            print_camera_settings(self.camera)
            
            self.statusBar().showMessage("Camera connected successfully")
            self.start_button.setEnabled(True)
            self.reconnect_button.setEnabled(True)
            
            return True
            
        except CameraNotFoundError as e:
            QMessageBox.critical(
                self,
                "Camera Not Found",
                f"No camera detected.\n\n{str(e)}\n\nPlease ensure:\n"
                "1. Camera is connected via USB\n"
                "2. Basler Pylon SDK is installed\n"
                "3. Camera drivers are installed"
            )
            self.statusBar().showMessage("Camera not found")
            return False
            
        except CameraConnectionError as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to camera.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Connection failed")
            return False

        except CameraConfigurationError as e:
            QMessageBox.critical(
                self,
                "Camera Configuration",
                f"The camera connected but settings could not be applied.\n\n{str(e)}\n\n"
                "Try adjusting resolution or exposure in config/camera_defaults.json "
                "to match your camera model.",
            )
            self.statusBar().showMessage("Camera configuration failed")
            if self.camera:
                try:
                    self.camera.disconnect()
                except Exception:
                    pass
                self.camera = None
            return False
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during camera initialization.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Initialization error")
            return False
    
    def start_preview(self) -> None:
        """Start camera preview."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected. Please initialize camera first."
            )
            return
        
        try:
            self.camera.start_grabbing()
            self.preview_timer.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.capture_button.setEnabled(True)
            
            self.statusBar().showMessage("Preview running...")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start preview.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Preview start failed")
    
    def stop_preview(self) -> None:
        """Stop camera preview."""
        if self.preview_timer:
            self.preview_timer.stop()
        
        if self.camera:
            try:
                self.camera.stop_grabbing()
            except Exception:
                pass
        
        self.preview_widget.clear_display()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        
        self.statusBar().showMessage("Preview stopped")
    
    def update_preview(self) -> None:
        """Update preview with latest frame."""
        if not self.camera or not self.camera.is_grabbing:
            return
        
        try:
            # Grab preview frame (1920x1080)
            frame = self.camera.grab_preview_frame(
                self._preview_width, self._preview_height
            )
            
            if frame is not None:
                self.preview_widget.display_frame(frame)
            else:
                # Frame grab failed, but don't show error for every failed frame
                pass
                
        except CameraGrabError:
            # Handle grab errors silently during preview
            pass
        except Exception:
            # Other errors - stop preview
            self.stop_preview()
            QMessageBox.warning(
                self,
                "Preview Error",
                "An error occurred during preview. Preview stopped."
            )
    
    def capture_image(self) -> None:
        """Capture a full-resolution image and save it under the configured storage folder."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected."
            )
            return
        
        try:
            self.statusBar().showMessage("Capturing image...")
            
            frame = self.camera.grab_frame()
            
            if frame is None:
                self.statusBar().showMessage("Capture failed")
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture image. Please try again."
                )
                return

            result = self._snapshot_writer.save_bgr(frame, prefix="capture")
            self.statusBar().showMessage(f"Saved: {result.path.name}")

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Capture saved")
            msg.setText(
                f"Resolution: {result.width}×{result.height}\n\n"
                f"{result.path}"
            )
            open_folder = msg.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()
            if msg.clickedButton() == open_folder:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.path.parent)))
                
        except CameraGrabError as e:
            QMessageBox.warning(
                self,
                "Capture Error",
                f"Failed to capture image.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")
        except (OSError, ValueError, RuntimeError) as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"The image was grabbed but could not be saved.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Save error")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during capture.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")

    def reconnect_camera(self) -> None:
        """Disconnect and reconnect the camera using the last successful configuration."""
        if not self.camera_config:
            QMessageBox.warning(
                self,
                "Reconnect",
                "No camera configuration is loaded.",
            )
            return

        was_preview = self.camera is not None and self.camera.is_grabbing
        self.stop_preview()

        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass
            self.camera = None

        self.start_button.setEnabled(False)
        self.reconnect_button.setEnabled(False)
        self.statusBar().showMessage("Reconnecting…")

        if self.initialize_camera(self.camera_config) and was_preview:
            self.start_preview()
    
    def _update_settings_ui(self) -> None:
        """Update UI controls with current camera settings."""
        if not self.camera or not self.camera.is_connected:
            return
        
        self._updating_settings = True
        
        try:
            # Get current exposure settings
            exp_auto, exp_value = self.camera.get_exposure()
            self.exposure_auto_checkbox.setChecked(exp_auto)
            if not exp_auto and exp_value > 0:
                self.exposure_slider.setValue(exp_value)
                self.exposure_spinbox.setValue(exp_value)
            self.exposure_slider.setEnabled(not exp_auto)
            self.exposure_spinbox.setEnabled(not exp_auto)
            
            # Get current gain settings
            gain_auto, gain_value = self.camera.get_gain()
            self.gain_auto_checkbox.setChecked(gain_auto)
            if not gain_auto and gain_value > 0:
                self.gain_slider.setValue(int(gain_value * 10))
                self.gain_spinbox.setValue(gain_value)
            self.gain_slider.setEnabled(not gain_auto)
            self.gain_spinbox.setEnabled(not gain_auto)
            
            # Get current white balance
            try:
                wb_auto = self.camera.get_white_balance()
                self.white_balance_auto_checkbox.setChecked(wb_auto)
            except Exception:
                # White balance not supported
                self.white_balance_auto_checkbox.setEnabled(False)
            
            # Get current frame rate
            try:
                frame_rate = self.camera.get_frame_rate()
                if frame_rate > 0:
                    self.frame_rate_spinbox.setValue(frame_rate)
            except Exception:
                pass
            
            # Get current gamma
            try:
                gamma = self.camera.get_gamma()
                if gamma is not None:
                    self.gamma_slider.setValue(int(gamma * 100))
                    self.gamma_spinbox.setValue(gamma)
            except Exception:
                # Gamma not supported, disable controls
                self.gamma_slider.setEnabled(False)
                self.gamma_spinbox.setEnabled(False)
            
        finally:
            self._updating_settings = False
    
    def on_exposure_auto_changed(self, state: int) -> None:
        """Handle exposure auto checkbox change."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        
        auto = state == Qt.CheckState.Checked
        self.exposure_slider.setEnabled(not auto)
        self.exposure_spinbox.setEnabled(not auto)
        
        if auto:
            try:
                self.camera.set_exposure(0, auto=True)
                self.statusBar().showMessage("Exposure: Auto")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set auto-exposure: {e}")
        else:
            # Use current slider value
            self.on_exposure_changed(self.exposure_slider.value())
    
    def on_exposure_changed(self, value: int) -> None:
        """Handle exposure slider change."""
        if self._updating_settings:
            return
        
        self.exposure_spinbox.blockSignals(True)
        self.exposure_spinbox.setValue(value)
        self.exposure_spinbox.blockSignals(False)
        
        if not self.exposure_auto_checkbox.isChecked() and self.camera and self.camera.is_connected:
            try:
                self.camera.set_exposure(value, auto=False)
                self.statusBar().showMessage(f"Exposure: {value/1000:.1f} ms")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set exposure: {e}")
    
    def on_exposure_spinbox_changed(self, value: int) -> None:
        """Handle exposure spinbox change."""
        if self._updating_settings:
            return
        
        self.exposure_slider.blockSignals(True)
        self.exposure_slider.setValue(value)
        self.exposure_slider.blockSignals(False)
        
        if not self.exposure_auto_checkbox.isChecked() and self.camera and self.camera.is_connected:
            try:
                self.camera.set_exposure(value, auto=False)
                self.statusBar().showMessage(f"Exposure: {value/1000:.1f} ms")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set exposure: {e}")
    
    def on_gain_auto_changed(self, state: int) -> None:
        """Handle gain auto checkbox change."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        
        auto = state == Qt.CheckState.Checked
        self.gain_slider.setEnabled(not auto)
        self.gain_spinbox.setEnabled(not auto)
        
        if auto:
            try:
                self.camera.set_gain(0.0, auto=True)
                self.statusBar().showMessage("Gain: Auto")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set auto-gain: {e}")
        else:
            # Use current slider value
            self.on_gain_changed(self.gain_slider.value())
    
    def on_gain_changed(self, value: int) -> None:
        """Handle gain slider change."""
        if self._updating_settings:
            return
        
        gain_value = value / 10.0
        self.gain_spinbox.blockSignals(True)
        self.gain_spinbox.setValue(gain_value)
        self.gain_spinbox.blockSignals(False)
        
        if not self.gain_auto_checkbox.isChecked() and self.camera and self.camera.is_connected:
            try:
                self.camera.set_gain(gain_value, auto=False)
                self.statusBar().showMessage(f"Gain: {gain_value:.1f}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set gain: {e}")
    
    def on_gain_spinbox_changed(self, value: float) -> None:
        """Handle gain spinbox change."""
        if self._updating_settings:
            return
        
        slider_value = int(value * 10)
        self.gain_slider.blockSignals(True)
        self.gain_slider.setValue(slider_value)
        self.gain_slider.blockSignals(False)
        
        if not self.gain_auto_checkbox.isChecked() and self.camera and self.camera.is_connected:
            try:
                self.camera.set_gain(value, auto=False)
                self.statusBar().showMessage(f"Gain: {value:.1f}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to set gain: {e}")
    
    def on_white_balance_auto_changed(self, state: int) -> None:
        """Handle white balance auto checkbox change."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        
        auto = state == Qt.CheckState.Checked
        
        try:
            self.camera.set_white_balance(auto=auto)
            self.statusBar().showMessage(f"White Balance: {'Auto' if auto else 'Manual'}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set white balance: {e}")
            # Revert checkbox if failed
            self.white_balance_auto_checkbox.blockSignals(True)
            self.white_balance_auto_checkbox.setChecked(not auto)
            self.white_balance_auto_checkbox.blockSignals(False)
    
    def on_frame_rate_changed(self, value: float) -> None:
        """Handle frame rate spinbox change."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        
        try:
            self.camera.set_frame_rate(value)
            self.statusBar().showMessage(f"Frame Rate: {value:.1f} fps")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set frame rate: {e}")
    
    def on_gamma_changed(self, value: int) -> None:
        """Handle gamma slider change."""
        if self._updating_settings:
            return
        
        gamma_value = value / 100.0
        self.gamma_spinbox.blockSignals(True)
        self.gamma_spinbox.setValue(gamma_value)
        self.gamma_spinbox.blockSignals(False)
        
        if self.camera and self.camera.is_connected:
            try:
                self.camera.set_gamma(gamma_value)
                self.statusBar().showMessage(f"Gamma: {gamma_value:.2f}")
            except Exception as e:
                # Gamma not supported, silently fail
                pass
    
    def on_gamma_spinbox_changed(self, value: float) -> None:
        """Handle gamma spinbox change."""
        if self._updating_settings:
            return
        
        slider_value = int(value * 100)
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(slider_value)
        self.gamma_slider.blockSignals(False)
        
        if self.camera and self.camera.is_connected:
            try:
                self.camera.set_gamma(value)
                self.statusBar().showMessage(f"Gamma: {value:.2f}")
            except Exception as e:
                # Gamma not supported, silently fail
                pass
    
    def diagnose_blur(self) -> None:
        """Diagnose potential blur issues."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected."
            )
            return
        
        issues = diagnose_blur_issues(self.camera)
        
        message = "Blur Diagnosis:\n\n"
        if len(issues) == 1 and "No obvious software issues" in issues[0]:
            message += "✓ " + issues[0] + "\n\n"
            message += "Recommendations:\n"
            message += "1. Check physical camera lens focus\n"
            message += "2. Ensure camera is stable (no vibration)\n"
            message += "3. Check if lens cap is removed\n"
            message += "4. Verify camera is at correct distance from subject"
        else:
            message += "Potential Issues:\n"
            for issue in issues:
                message += f"• {issue}\n"
            message += "\nRecommendations:\n"
            message += "1. Adjust exposure time if motion blur detected\n"
            message += "2. Check physical camera lens focus\n"
            message += "3. Ensure adequate lighting\n"
            message += "4. Verify camera resolution settings"
        
        QMessageBox.information(self, "Blur Diagnosis", message)
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.stop_preview()
        
        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass
        
        event.accept()
