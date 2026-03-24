"""Preview widget for displaying camera feed and ROI editing."""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
import cv2


class PreviewWidget(QLabel):
    """
    Widget for displaying camera preview frames.
    
    This widget automatically scales and displays camera frames
    while maintaining aspect ratio.
    """
    
    # Signal emitted when frame is displayed
    frame_displayed = pyqtSignal()
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
        self._roi_mode = False
        self._roi_norm: Optional[tuple[float, float, float, float]] = None
        self._drag_kind: Optional[str] = None
        self._drag_start = QPointF()
        self._drag_roi_start: Optional[QRectF] = None
        self._new_roi_anchor: Optional[QPointF] = None
        self._roi_handle_radius = 7.0
        self._roi_min_norm = 0.06
        self.setMouseTracking(True)

    def set_show_grid(self, on: bool) -> None:
        self._show_grid = bool(on)

    def set_show_crosshair(self, on: bool) -> None:
        self._show_crosshair = bool(on)

    def set_auto_scale_preview(self, on: bool) -> None:
        self._auto_scale_preview = bool(on)

    def set_roi_mode(self, on: bool) -> None:
        self._roi_mode = bool(on)
        self.setCursor(Qt.CursorShape.CrossCursor if on else Qt.CursorShape.ArrowCursor)
        if on and self._roi_norm is None:
            self.recenter_roi()
        self.update()

    def recenter_roi(self) -> None:
        """Create/recenter ROI to a comfortable default box."""
        self._roi_norm = (0.25, 0.25, 0.5, 0.5)
        self._emit_roi_changed()
        self.update()

    def clear_roi(self) -> None:
        self._roi_norm = None
        self.update()

    def has_roi(self) -> bool:
        return self._roi_norm is not None

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
        self.update()
    
    def clear_display(self) -> None:
        """Clear the display."""
        self.setText("No camera feed")
        self.current_frame = None
        self.setPixmap(QPixmap())
        self.clear_roi()
    
    def resizeEvent(self, event) -> None:
        """Handle widget resize to update frame display."""
        super().resizeEvent(event)
        # Redisplay current frame if available
        if self.current_frame is not None:
            self.display_frame(self.current_frame)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._roi_norm is None:
            return
        frame_rect = self._frame_draw_rect()
        if frame_rect.isEmpty():
            return
        roi_rect = self._roi_rect_pixels(frame_rect)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Subtle dim around ROI for user guidance.
        dim = QColor(0, 0, 0, 44 if self._roi_mode else 26)
        p.fillRect(QRectF(frame_rect.left(), frame_rect.top(), frame_rect.width(), roi_rect.top() - frame_rect.top()), dim)
        p.fillRect(QRectF(frame_rect.left(), roi_rect.bottom(), frame_rect.width(), frame_rect.bottom() - roi_rect.bottom()), dim)
        p.fillRect(QRectF(frame_rect.left(), roi_rect.top(), roi_rect.left() - frame_rect.left(), roi_rect.height()), dim)
        p.fillRect(QRectF(roi_rect.right(), roi_rect.top(), frame_rect.right() - roi_rect.right(), roi_rect.height()), dim)

        border = QPen(QColor(245, 245, 245, 230), 2)
        p.setPen(border)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(roi_rect, 6, 6)

        if self._roi_mode:
            p.setBrush(QColor(255, 255, 255, 230))
            p.setPen(QPen(QColor(80, 86, 92, 240), 1))
            for hp in self._roi_handle_points(roi_rect):
                p.drawEllipse(hp, self._roi_handle_radius, self._roi_handle_radius)
        p.end()

    def mousePressEvent(self, event) -> None:
        if not self._roi_mode or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        frame_rect = self._frame_draw_rect()
        p = QPointF(event.position())
        if frame_rect.isEmpty() or not frame_rect.contains(p):
            return
        self._drag_start = p
        roi = self._roi_rect_pixels(frame_rect) if self._roi_norm is not None else None
        self._drag_kind = None
        self._drag_roi_start = roi

        if roi is not None:
            hit = self._hit_test_handle(roi, p)
            if hit is not None:
                self._drag_kind = hit
            elif roi.contains(p):
                self._drag_kind = "move"
        if self._drag_kind is None:
            self._drag_kind = "new"
            self._new_roi_anchor = p
            self._roi_norm = self._norm_from_points(frame_rect, p, p)
            self._emit_roi_changed()
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if not self._roi_mode or self._drag_kind is None:
            return super().mouseMoveEvent(event)
        frame_rect = self._frame_draw_rect()
        if frame_rect.isEmpty():
            return
        p = QPointF(event.position())
        p.setX(min(max(p.x(), frame_rect.left()), frame_rect.right()))
        p.setY(min(max(p.y(), frame_rect.top()), frame_rect.bottom()))

        if self._drag_kind == "new" and self._new_roi_anchor is not None:
            self._roi_norm = self._norm_from_points(frame_rect, self._new_roi_anchor, p)
        else:
            roi0 = self._drag_roi_start
            if roi0 is None:
                return
            dx = p.x() - self._drag_start.x()
            dy = p.y() - self._drag_start.y()
            roi = QRectF(roi0)
            if self._drag_kind == "move":
                roi.translate(dx, dy)
                roi = self._clamp_rect(roi, frame_rect)
            else:
                self._resize_rect_by_handle(roi, self._drag_kind, dx, dy)
                roi = self._clamp_rect(roi.normalized(), frame_rect)
                roi = self._enforce_min_size(roi, frame_rect)
            self._roi_norm = self._rect_to_norm(frame_rect, roi)
        self._emit_roi_changed()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_kind is not None and self._roi_norm is not None:
            self._roi_norm = self._normalized_norm(self._roi_norm)
            self._emit_roi_changed()
        self._drag_kind = None
        self._drag_roi_start = None
        self._new_roi_anchor = None
        super().mouseReleaseEvent(event)

    def _frame_draw_rect(self) -> QRectF:
        pm = self.pixmap()
        if pm is None or pm.isNull():
            return QRectF()
        pw = float(pm.width())
        ph = float(pm.height())
        x = (self.width() - pw) / 2.0
        y = (self.height() - ph) / 2.0
        return QRectF(x, y, pw, ph)

    def _roi_rect_pixels(self, frame_rect: QRectF) -> QRectF:
        if self._roi_norm is None:
            return QRectF()
        nx, ny, nw, nh = self._roi_norm
        return QRectF(
            frame_rect.left() + nx * frame_rect.width(),
            frame_rect.top() + ny * frame_rect.height(),
            nw * frame_rect.width(),
            nh * frame_rect.height(),
        )

    def _rect_to_norm(self, frame_rect: QRectF, rect: QRectF) -> tuple[float, float, float, float]:
        return self._normalized_norm(
            (
                (rect.left() - frame_rect.left()) / max(1.0, frame_rect.width()),
                (rect.top() - frame_rect.top()) / max(1.0, frame_rect.height()),
                rect.width() / max(1.0, frame_rect.width()),
                rect.height() / max(1.0, frame_rect.height()),
            )
        )

    def _norm_from_points(self, frame_rect: QRectF, a: QPointF, b: QPointF) -> tuple[float, float, float, float]:
        rect = QRectF(a, b).normalized()
        rect = self._clamp_rect(rect, frame_rect)
        rect = self._enforce_min_size(rect, frame_rect)
        return self._rect_to_norm(frame_rect, rect)

    def _normalized_norm(self, roi: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        x, y, w, h = roi
        x = max(0.0, min(1.0 - self._roi_min_norm, x))
        y = max(0.0, min(1.0 - self._roi_min_norm, y))
        w = max(self._roi_min_norm, min(1.0 - x, w))
        h = max(self._roi_min_norm, min(1.0 - y, h))
        return (x, y, w, h)

    def _clamp_rect(self, rect: QRectF, bounds: QRectF) -> QRectF:
        r = QRectF(rect)
        if r.left() < bounds.left():
            r.moveLeft(bounds.left())
        if r.top() < bounds.top():
            r.moveTop(bounds.top())
        if r.right() > bounds.right():
            r.moveRight(bounds.right())
        if r.bottom() > bounds.bottom():
            r.moveBottom(bounds.bottom())
        return r

    def _enforce_min_size(self, rect: QRectF, bounds: QRectF) -> QRectF:
        min_w = self._roi_min_norm * bounds.width()
        min_h = self._roi_min_norm * bounds.height()
        r = QRectF(rect)
        if r.width() < min_w:
            r.setWidth(min_w)
        if r.height() < min_h:
            r.setHeight(min_h)
        return self._clamp_rect(r, bounds)

    def _roi_handle_points(self, rect: QRectF) -> list[QPointF]:
        return [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight(),
        ]

    def _hit_test_handle(self, rect: QRectF, p: QPointF) -> Optional[str]:
        handles = {
            "resize_tl": rect.topLeft(),
            "resize_tr": rect.topRight(),
            "resize_bl": rect.bottomLeft(),
            "resize_br": rect.bottomRight(),
        }
        for name, hp in handles.items():
            if (hp.x() - p.x()) ** 2 + (hp.y() - p.y()) ** 2 <= (self._roi_handle_radius + 4) ** 2:
                return name
        return None

    @staticmethod
    def _resize_rect_by_handle(rect: QRectF, kind: str, dx: float, dy: float) -> None:
        if kind == "resize_tl":
            rect.setTopLeft(rect.topLeft() + QPointF(dx, dy))
        elif kind == "resize_tr":
            rect.setTopRight(rect.topRight() + QPointF(dx, dy))
        elif kind == "resize_bl":
            rect.setBottomLeft(rect.bottomLeft() + QPointF(dx, dy))
        elif kind == "resize_br":
            rect.setBottomRight(rect.bottomRight() + QPointF(dx, dy))

    def _emit_roi_changed(self) -> None:
        if self._roi_norm is None:
            return
        x, y, w, h = self._roi_norm
        self.roi_changed.emit(x, y, w, h)
