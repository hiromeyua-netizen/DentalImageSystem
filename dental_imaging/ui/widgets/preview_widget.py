"""
Preview widget for displaying camera feed.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
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
        self._show_grid = False
        self._show_crosshair = False
        self._auto_scale_preview = True

    def set_show_grid(self, on: bool) -> None:
        self._show_grid = bool(on)

    def set_show_crosshair(self, on: bool) -> None:
        self._show_crosshair = bool(on)

    def set_auto_scale_preview(self, on: bool) -> None:
        self._auto_scale_preview = bool(on)

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
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)

        h, w, ch = rgb_frame.shape
        if self._show_crosshair:
            cx, cy = w // 2, h // 2
            cv2.line(rgb_frame, (cx, 0), (cx, h - 1), (255, 255, 255), 1)
            cv2.line(rgb_frame, (0, cy), (w - 1, cy), (255, 255, 255), 1)
        if self._show_grid:
            for g in range(1, 8):
                xi = g * w // 8
                yi = g * h // 8
                cv2.line(
                    rgb_frame,
                    (xi, 0),
                    (xi, h - 1),
                    (72, 72, 80),
                    1,
                    cv2.LINE_AA,
                )
                cv2.line(
                    rgb_frame,
                    (0, yi),
                    (w - 1, yi),
                    (72, 72, 80),
                    1,
                    cv2.LINE_AA,
                )
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        
        pixmap = QPixmap.fromImage(qt_image)
        cw, ch_box = max(1, self.width()), max(1, self.height())
        pw, ph = pixmap.width(), pixmap.height()

        if self._auto_scale_preview:
            if pw > cw or ph > ch_box:
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation,
                )
            else:
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
        else:
            if pw <= cw and ph <= ch_box:
                scaled_pixmap = pixmap
            else:
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation,
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
