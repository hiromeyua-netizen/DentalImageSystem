"""
Preview widget for displaying camera feed.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent
import cv2


class PreviewWidget(QLabel):
    """
    Widget for displaying camera preview frames.
    
    This widget automatically scales and displays camera frames
    while maintaining aspect ratio.
    """
    
    # Signal emitted when frame is displayed
    frame_displayed = pyqtSignal()
    # Normalized ROI rectangle (x, y, w, h) in [0,1]
    roi_changed = pyqtSignal(float, float, float, float)
    
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
        self._roi_mode_enabled = False
        self._roi_norm: Optional[tuple[float, float, float, float]] = None
        self._drag_start: Optional[tuple[float, float]] = None
        self._drag_current: Optional[tuple[float, float]] = None
        self._last_frame_size: tuple[int, int] = (1, 1)
        self._last_pixmap_rect: tuple[int, int, int, int] = (0, 0, 1, 1)

    def set_show_grid(self, on: bool) -> None:
        self._show_grid = bool(on)

    def set_show_crosshair(self, on: bool) -> None:
        self._show_crosshair = bool(on)

    def set_auto_scale_preview(self, on: bool) -> None:
        self._auto_scale_preview = bool(on)

    def set_roi_mode(self, enabled: bool) -> None:
        self._roi_mode_enabled = bool(enabled)
        if not enabled:
            self._drag_start = None
            self._drag_current = None

    def set_roi(self, roi_norm: Optional[tuple[float, float, float, float]]) -> None:
        self._roi_norm = roi_norm

    def clear_roi(self) -> None:
        self._roi_norm = None

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
        self._last_frame_size = (w, h)
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
        if self._roi_norm is not None:
            rx, ry, rw, rh = self._roi_norm
            x0 = int(max(0, min(w - 1, rx * w)))
            y0 = int(max(0, min(h - 1, ry * h)))
            x1 = int(max(0, min(w - 1, (rx + rw) * w)))
            y1 = int(max(0, min(h - 1, (ry + rh) * h)))
            cv2.rectangle(rgb_frame, (x0, y0), (x1, y1), (230, 230, 230), 2)
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
        px = (self.width() - scaled_pixmap.width()) // 2
        py = (self.height() - scaled_pixmap.height()) // 2
        self._last_pixmap_rect = (px, py, scaled_pixmap.width(), scaled_pixmap.height())
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

    def _widget_to_norm(self, x: int, y: int) -> Optional[tuple[float, float]]:
        px, py, pw, ph = self._last_pixmap_rect
        if pw <= 0 or ph <= 0:
            return None
        if x < px or y < py or x > px + pw or y > py + ph:
            return None
        nx = (x - px) / float(pw)
        ny = (y - py) / float(ph)
        return (max(0.0, min(1.0, nx)), max(0.0, min(1.0, ny)))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._roi_mode_enabled and event.button() == Qt.MouseButton.LeftButton:
            p = self._widget_to_norm(event.position().x(), event.position().y())
            if p is not None:
                self._drag_start = p
                self._drag_current = p
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._roi_mode_enabled and self._drag_start is not None:
            p = self._widget_to_norm(event.position().x(), event.position().y())
            if p is not None:
                self._drag_current = p
                sx, sy = self._drag_start
                cx, cy = self._drag_current
                x0, y0 = min(sx, cx), min(sy, cy)
                x1, y1 = max(sx, cx), max(sy, cy)
                self._roi_norm = (x0, y0, max(0.01, x1 - x0), max(0.01, y1 - y0))
                if self.current_frame is not None:
                    self.display_frame(self.current_frame)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            self._roi_mode_enabled
            and self._drag_start is not None
            and event.button() == Qt.MouseButton.LeftButton
        ):
            if self._roi_norm is not None:
                rx, ry, rw, rh = self._roi_norm
                self.roi_changed.emit(rx, ry, rw, rh)
            self._drag_start = None
            self._drag_current = None
            return
        super().mouseReleaseEvent(event)
