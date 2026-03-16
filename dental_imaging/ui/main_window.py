"""
Main application window.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from dental_imaging.hardware.camera import BaslerCamera, get_first_available_camera
from dental_imaging.ui.widgets.preview_widget import PreviewWidget
from dental_imaging.core.config_manager import ConfigManager
from dental_imaging.exceptions import (
    CameraNotFoundError,
    CameraConnectionError,
    CameraInitializationError
)


class MainWindow(QMainWindow):
    """
    Main application window for the dental imaging system.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera: Optional[BaslerCamera] = None
        self.config_manager = ConfigManager()
        
        # Load configuration
        try:
            self.default_config = self.config_manager.get_default_config()
            self.camera_config = self.config_manager.get_camera_config()
            self.preview_width, self.preview_height = self.config_manager.get_preview_resolution()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to load configuration: {str(e)}"
            )
            raise
        
        # Setup UI
        self.setup_ui()
        
        # Initialize camera
        self.init_camera()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Dental Imaging System")
        
        # Set window to fullscreen if kiosk mode is enabled
        if self.default_config.get("application", {}).get("kiosk_mode", False):
            self.showFullScreen()
        else:
            self.resize(1280, 720)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Preview widget
        self.preview_widget = PreviewWidget(self)
        self.preview_widget.set_preview_size(self.preview_width, self.preview_height)
        self.preview_widget.camera_error.connect(self.on_camera_error)
        main_layout.addWidget(self.preview_widget, stretch=1)
        
        # Control panel
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # Start/Stop Preview button
        self.preview_button = QPushButton("Start Preview")
        self.preview_button.setMinimumHeight(50)
        self.preview_button.setFont(QFont("Arial", 12))
        self.preview_button.clicked.connect(self.toggle_preview)
        control_layout.addWidget(self.preview_button)
        
        # Capture button (disabled for now, will be implemented later)
        self.capture_button = QPushButton("Capture")
        self.capture_button.setMinimumHeight(50)
        self.capture_button.setFont(QFont("Arial", 12))
        self.capture_button.setEnabled(False)
        control_layout.addWidget(self.capture_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        control_layout.addWidget(self.status_label, stretch=1)
        
        main_layout.addLayout(control_layout)
        
        # Status bar
        self.statusBar().showMessage("Initializing...")
    
    def init_camera(self):
        """Initialize camera connection."""
        try:
            self.statusBar().showMessage("Detecting camera...")
            self.status_label.setText("Detecting camera...")
            
            # Get first available camera
            camera_info = get_first_available_camera()
            
            if not camera_info:
                raise CameraNotFoundError("No camera detected")
            
            self.statusBar().showMessage(f"Connecting to {camera_info.model_name}...")
            self.status_label.setText(f"Connecting to {camera_info.model_name}...")
            
            # Create and connect camera
            self.camera = BaslerCamera(camera_info)
            self.camera.connect()
            
            # Configure camera
            self.statusBar().showMessage("Configuring camera...")
            self.status_label.setText("Configuring camera...")
            self.camera.configure(self.camera_config)
            
            # Set camera in preview widget
            self.preview_widget.set_camera(self.camera)
            
            self.statusBar().showMessage("Camera ready")
            self.status_label.setText("Camera ready - Click 'Start Preview' to begin")
            self.preview_button.setEnabled(True)
            
        except CameraNotFoundError as e:
            self.statusBar().showMessage("Camera not found")
            self.status_label.setText("Camera not found")
            QMessageBox.warning(
                self,
                "Camera Not Found",
                f"No camera detected.\n\n{str(e)}\n\n"
                "Please ensure:\n"
                "1. Basler camera is connected via USB\n"
                "2. Basler Pylon SDK is installed\n"
                "3. Camera drivers are installed"
            )
            self.preview_button.setEnabled(False)
            
        except (CameraConnectionError, CameraInitializationError) as e:
            self.statusBar().showMessage("Camera connection failed")
            self.status_label.setText("Camera connection failed")
            QMessageBox.critical(
                self,
                "Camera Connection Error",
                f"Failed to connect to camera:\n\n{str(e)}"
            )
            self.preview_button.setEnabled(False)
            
        except Exception as e:
            self.statusBar().showMessage("Initialization error")
            self.status_label.setText("Initialization error")
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"An error occurred during initialization:\n\n{str(e)}"
            )
            self.preview_button.setEnabled(False)
    
    @pyqtSlot()
    def toggle_preview(self):
        """Toggle preview on/off."""
        if self.preview_widget.is_previewing:
            self.stop_preview()
        else:
            self.start_preview()
    
    def start_preview(self):
        """Start camera preview."""
        try:
            self.preview_widget.start_preview()
            self.preview_button.setText("Stop Preview")
            self.statusBar().showMessage("Preview active")
            self.status_label.setText("Preview active")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Preview Error",
                f"Failed to start preview:\n\n{str(e)}"
            )
    
    def stop_preview(self):
        """Stop camera preview."""
        self.preview_widget.stop_preview()
        self.preview_button.setText("Start Preview")
        self.statusBar().showMessage("Preview stopped")
        self.status_label.setText("Preview stopped")
    
    @pyqtSlot(str)
    def on_camera_error(self, error_message: str):
        """Handle camera errors from preview widget."""
        self.statusBar().showMessage(f"Error: {error_message}")
        self.status_label.setText(f"Error: {error_message}")
        
        # Stop preview on error
        if self.preview_widget.is_previewing:
            self.stop_preview()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop preview
        if self.preview_widget.is_previewing:
            self.stop_preview()
        
        # Disconnect camera
        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass  # Ignore errors during cleanup
        
        event.accept()
