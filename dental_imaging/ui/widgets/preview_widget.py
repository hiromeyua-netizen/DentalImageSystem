"""
Preview widget for displaying camera feed and interactive ROI editing.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
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
    # Emitted when ROI changes (x, y, w, h) in frame coordinates.
    roi_changed = pyqtSignal(tuple)
    
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
        self._display_origin = QPoint(0, 0)
        self._display_size = (1, 1)

        # ROI state
        self._roi_rect: Optional[tuple[int, int, int, int]] = None
        self._roi_edit_mode = False
        self._roi_min_size = 32
        self._drag_mode: Optional[str] = None  # create | move | resize_nw/ne/sw/se
        self._drag_anchor: Optional[tuple[int, int]] = None
        self._last_drag_point: Optional[tuple[int, int]] = None

    def set_show_grid(self, on: bool) -> None:
        self._show_grid = bool(on)

    def set_show_crosshair(self, on: bool) -> None:
        self._show_crosshair = bool(on)

    def set_auto_scale_preview(self, on: bool) -> None:
        self._auto_scale_preview = bool(on)

    def set_roi_mode(self, enabled: bool) -> None:
        """Enable or disable interactive ROI edit mode."""
        self._roi_edit_mode = bool(enabled)
        if self._roi_edit_mode and self._roi_rect is None:
            self.recenter_roi()
        if not self._roi_edit_mode:
            self._drag_mode = None
            self._drag_anchor = None
            self._last_drag_point = None
        self._redraw_current()

    def recenter_roi(self) -> None:
        """Create or move ROI to centered default box."""
        if self.current_frame is None or self.current_frame.size == 0:
            return
        fh, fw = self.current_frame.shape[:2]
        rw = max(self._roi_min_size, int(fw * 0.42))
        rh = max(self._roi_min_size, int(fh * 0.42))
        x = (fw - rw) // 2
        y = (fh - rh) // 2
        self._roi_rect = (x, y, rw, rh)
        self.roi_changed.emit(self._roi_rect)
        self._redraw_current()

    def roi_rect(self) -> Optional[tuple[int, int, int, int]]:
        return self._roi_rect

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
        self._draw_roi_overlay(rgb_frame)
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
        self._display_origin = QPoint(
            (self.width() - scaled_pixmap.width()) // 2,
            (self.height() - scaled_pixmap.height()) // 2,
        )
        self._display_size = (max(1, scaled_pixmap.width()), max(1, scaled_pixmap.height()))
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

    def mousePressEvent(self, event) -> None:
        if not self._roi_edit_mode or self.current_frame is None:
            return super().mousePressEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        p = self._widget_to_frame(event.position().toPoint())
        if p is None:
            return
        fx, fy = p
        self._drag_mode = self._pick_drag_mode(fx, fy)
        if self._drag_mode == "create":
            self._drag_anchor = (fx, fy)
            self._roi_rect = (fx, fy, self._roi_min_size, self._roi_min_size)
        self._last_drag_point = (fx, fy)
        self._redraw_current()

    def mouseMoveEvent(self, event) -> None:
        if not self._roi_edit_mode or self.current_frame is None or self._drag_mode is None:
            return super().mouseMoveEvent(event)
        p = self._widget_to_frame(event.position().toPoint())
        if p is None:
            return
        fx, fy = p
        if self._drag_mode == "create" and self._drag_anchor is not None:
            ax, ay = self._drag_anchor
            self._roi_rect = self._rect_from_points(ax, ay, fx, fy)
        elif self._drag_mode == "move" and self._roi_rect and self._last_drag_point:
            lx, ly = self._last_drag_point
            dx, dy = fx - lx, fy - ly
            self._roi_rect = self._move_rect(self._roi_rect, dx, dy)
        elif self._drag_mode and self._drag_mode.startswith("resize_") and self._roi_rect:
            self._roi_rect = self._resize_rect(self._roi_rect, self._drag_mode, fx, fy)
        self._last_drag_point = (fx, fy)
        if self._roi_rect:
            self.roi_changed.emit(self._roi_rect)
        self._redraw_current()

    def mouseReleaseEvent(self, event) -> None:
        if not self._roi_edit_mode:
            return super().mouseReleaseEvent(event)
        if self._roi_rect:
            self._roi_rect = self._clamp_rect(self._roi_rect)
            self.roi_changed.emit(self._roi_rect)
            self._redraw_current()
        self._drag_mode = None
        self._drag_anchor = None
        self._last_drag_point = None

    def _redraw_current(self) -> None:
        if self.current_frame is not None:
            self.display_frame(self.current_frame)

    def _draw_roi_overlay(self, rgb_frame: np.ndarray) -> None:
        if self._roi_rect is None or not self._roi_edit_mode:
            return
        fh, fw = rgb_frame.shape[:2]
        x, y, w, h = self._clamp_rect(self._roi_rect)
        self._roi_rect = (x, y, w, h)

        # Dim outside ROI for clear focus.
        overlay = rgb_frame.copy()
        cv2.rectangle(overlay, (0, 0), (fw - 1, fh - 1), (30, 30, 34), -1)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.18, rgb_frame, 0.82, 0, rgb_frame)

        color = (255, 255, 255) if self._roi_edit_mode else (220, 220, 225)
        cv2.rectangle(rgb_frame, (x, y), (x + w, y + h), color, 2)
        if self._roi_edit_mode:
            hs = max(4, min(10, min(fw, fh) // 120))
            for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
                cv2.rectangle(rgb_frame, (cx - hs, cy - hs), (cx + hs, cy + hs), color, -1)

    def _widget_to_frame(self, p: QPoint) -> Optional[tuple[int, int]]:
        if self.current_frame is None or self.current_frame.size == 0:
            return None
        ox, oy = self._display_origin.x(), self._display_origin.y()
        dw, dh = self._display_size
        if p.x() < ox or p.y() < oy or p.x() > ox + dw or p.y() > oy + dh:
            return None
        fh, fw = self.current_frame.shape[:2]
        rx = (p.x() - ox) / max(1, dw)
        ry = (p.y() - oy) / max(1, dh)
        fx = int(max(0, min(fw - 1, round(rx * (fw - 1)))))
        fy = int(max(0, min(fh - 1, round(ry * (fh - 1)))))
        return (fx, fy)

    def _pick_drag_mode(self, fx: int, fy: int) -> str:
        if self._roi_rect is None:
            return "create"
        x, y, w, h = self._roi_rect
        r = max(8, min(18, min(w, h) // 6))
        corners = {
            "resize_nw": (x, y),
            "resize_ne": (x + w, y),
            "resize_sw": (x, y + h),
            "resize_se": (x + w, y + h),
        }
        for mode, (cx, cy) in corners.items():
            if abs(fx - cx) <= r and abs(fy - cy) <= r:
                return mode
        if x <= fx <= x + w and y <= fy <= y + h:
            return "move"
        return "create"

    def _rect_from_points(self, x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
        x = min(x1, x2)
        y = min(y1, y2)
        w = max(self._roi_min_size, abs(x2 - x1))
        h = max(self._roi_min_size, abs(y2 - y1))
        return self._clamp_rect((x, y, w, h))

    def _move_rect(self, rect: tuple[int, int, int, int], dx: int, dy: int) -> tuple[int, int, int, int]:
        x, y, w, h = rect
        return self._clamp_rect((x + dx, y + dy, w, h))

    def _resize_rect(
        self, rect: tuple[int, int, int, int], mode: str, fx: int, fy: int
    ) -> tuple[int, int, int, int]:
        x, y, w, h = rect
        x2, y2 = x + w, y + h
        if mode == "resize_nw":
            x, y = fx, fy
        elif mode == "resize_ne":
            x2, y = fx, fy
        elif mode == "resize_sw":
            x, y2 = fx, fy
        elif mode == "resize_se":
            x2, y2 = fx, fy
        nx = min(x, x2)
        ny = min(y, y2)
        nw = max(self._roi_min_size, abs(x2 - x))
        nh = max(self._roi_min_size, abs(y2 - y))
        return self._clamp_rect((nx, ny, nw, nh))

    def _clamp_rect(self, rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        if self.current_frame is None or self.current_frame.size == 0:
            return rect
        x, y, w, h = rect
        fh, fw = self.current_frame.shape[:2]
        w = max(self._roi_min_size, min(w, fw))
        h = max(self._roi_min_size, min(h, fh))
        x = max(0, min(x, fw - w))
        y = max(0, min(y, fh - h))
        return (int(x), int(y), int(w), int(h))
