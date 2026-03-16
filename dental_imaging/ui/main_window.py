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
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from dental_imaging.ui.widgets.preview_widget import PreviewWidget
from dental_imaging.hardware.camera import BaslerCamera
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.exceptions import (
    CameraNotFoundError,
    CameraConnectionError,
    CameraGrabError,
)


class MainWindow(QMainWindow):
    """
    Main application window for dental imaging system.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera: Optional[BaslerCamera] = None
        self.camera_config: Optional[CameraConfig] = None
        self.preview_timer: Optional[QTimer] = None
        
        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Dental Imaging System - Camera Preview")
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
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def _setup_timers(self) -> None:
        """Set up timers for preview updates."""
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        # Update at ~30 FPS
        self.preview_timer.setInterval(33)  # ~30 FPS
        
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
            
            self.statusBar().showMessage("Camera connected successfully")
            self.start_button.setEnabled(True)
            
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
            frame = self.camera.grab_preview_frame(1920, 1080)
            
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
        """Capture a full-resolution image."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected."
            )
            return
        
        try:
            self.statusBar().showMessage("Capturing image...")
            
            # Grab full resolution frame
            frame = self.camera.grab_frame()
            
            if frame is not None:
                self.statusBar().showMessage(
                    f"Image captured! Shape: {frame.shape[1]}x{frame.shape[0]}"
                )
                # TODO: Save image to file
                QMessageBox.information(
                    self,
                    "Capture Success",
                    f"Image captured successfully!\n\n"
                    f"Resolution: {frame.shape[1]}x{frame.shape[0]}\n"
                    f"Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}"
                )
            else:
                self.statusBar().showMessage("Capture failed")
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture image. Please try again."
                )
                
        except CameraGrabError as e:
            QMessageBox.warning(
                self,
                "Capture Error",
                f"Failed to capture image.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during capture.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.stop_preview()
        
        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass
        
        event.accept()
