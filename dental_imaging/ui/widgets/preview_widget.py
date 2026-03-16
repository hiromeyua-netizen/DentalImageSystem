"""
Preview widget for displaying camera feed.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from dental_imaging.hardware.camera import BaslerCamera
from dental_imaging.exceptions import CameraConnectionError, CameraGrabError


class PreviewWidget(QWidget):
    """
    Widget for displaying live camera preview.
    
    This widget handles frame grabbing and display updates.
    """
    
    # Signal emitted when frame is updated
    frame_updated = pyqtSignal()
    
    # Signal emitted on camera errors
    camera_error = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize preview widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera: Optional[BaslerCamera] = None
        self.preview_width = 1920
        self.preview_height = 1080
        self.update_interval_ms = 33  # ~30 FPS
        
        # Setup UI
        self.setup_ui()
        
        # Timer for frame updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frame)
        
        self.is_previewing = False
    
    def setup_ui(self):
        """Setup the UI components."""
        # Create label for displaying image
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setText("No camera feed")
        
        # Set minimum size
        self.setMinimumSize(640, 480)
    
    def set_camera(self, camera: BaslerCamera):
        """
        Set the camera to use for preview.
        
        Args:
            camera: BaslerCamera instance
        """
        self.camera = camera
    
    def set_preview_size(self, width: int, height: int):
        """
        Set preview resolution.
        
        Args:
            width: Preview width
            height: Preview height
        """
        self.preview_width = width
        self.preview_height = height
    
    def start_preview(self):
        """Start the preview stream."""
        if not self.camera:
            self.camera_error.emit("No camera set")
            return
        
        if not self.camera.is_connected:
            self.camera_error.emit("Camera not connected")
            return
        
        try:
            # Start continuous grabbing
            if not self.camera.is_grabbing:
                self.camera.start_grabbing()
            
            # Start update timer
            self.update_timer.start(self.update_interval_ms)
            self.is_previewing = True
            
        except Exception as e:
            self.camera_error.emit(f"Failed to start preview: {str(e)}")
    
    def stop_preview(self):
        """Stop the preview stream."""
        self.update_timer.stop()
        self.is_previewing = False
        
        if self.camera and self.camera.is_grabbing:
            self.camera.stop_grabbing()
    
    def update_frame(self):
        """
        Update the preview frame.
        Called by the timer at regular intervals.
        """
        if not self.camera or not self.camera.is_connected:
            return
        
        try:
            # Grab preview frame
            frame = self.camera.grab_preview_frame(
                self.preview_width,
                self.preview_height
            )
            
            if frame is not None:
                self.display_frame(frame)
                self.frame_updated.emit()
            else:
                # Frame grab failed, but don't show error for every missed frame
                pass
                
        except CameraGrabError as e:
            self.camera_error.emit(f"Frame grab error: {str(e)}")
        except Exception as e:
            self.camera_error.emit(f"Preview error: {str(e)}")
    
    def display_frame(self, frame: np.ndarray):
        """
        Display a frame in the widget.
        
        Args:
            frame: numpy array (BGR format)
        """
        if frame is None or frame.size == 0:
            return
        
        # Convert numpy array to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB for Qt
        rgb_frame = np.flip(frame, axis=2)  # BGR to RGB
        
        q_image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
        # Convert to QPixmap and scale to fit label
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale pixmap to fit label while maintaining aspect ratio
        label_size = self.image_label.size()
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        # Resize image label to fill widget
        self.image_label.setGeometry(0, 0, self.width(), self.height())
    
    def closeEvent(self, event):
        """Handle widget close."""
        self.stop_preview()
        super().closeEvent(event)
