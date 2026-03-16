"""
Preview widget for displaying camera feed.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2


class PreviewWidget(QLabel):
    """
    Widget for displaying camera preview frames.
    
    This widget automatically scales and displays camera frames
    while maintaining aspect ratio.
    """
    
    # Signal emitted when frame is displayed
    frame_displayed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize preview widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black;")
        self.setText("No camera feed")
        
        self.current_frame: Optional[np.ndarray] = None
        self._aspect_ratio: float = 16.0 / 9.0  # Default aspect ratio
        
    def display_frame(self, frame: Optional[np.ndarray]) -> None:
        """
        Display a camera frame.
        
        Args:
            frame: numpy array (BGR format) or None to clear display
        """
        if frame is None:
            self.setText("No frame available")
            self.current_frame = None
            return
        
        self.current_frame = frame
        height, width = frame.shape[:2]
        self._aspect_ratio = width / height
        
        # Convert BGR to RGB for QImage
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage from numpy array
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
        # Scale pixmap to fit widget while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self.frame_displayed.emit()
    
    def clear_display(self) -> None:
        """Clear the display."""
        self.setText("No camera feed")
        self.current_frame = None
        self.setPixmap(QPixmap())
    
    def resizeEvent(self, event) -> None:
        """Handle widget resize to update frame display."""
        super().resizeEvent(event)
        # Redisplay current frame if available
        if self.current_frame is not None:
            self.display_frame(self.current_frame)
