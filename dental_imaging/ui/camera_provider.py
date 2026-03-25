"""
CameraFrameProvider — QQuickImageProvider that serves the latest camera frame
to the QML Image element via "image://camera/frame?<counter>".
"""
from __future__ import annotations

import threading

import numpy as np
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage
from PyQt6.QtQuick import QQuickImageProvider


class CameraFrameProvider(QQuickImageProvider):
    """Thread-safe image provider for live camera frames."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock  = threading.Lock()
        self._image = QImage(1920, 1080, QImage.Format.Format_RGB888)
        self._image.fill(0)

    def update_frame(self, bgr: np.ndarray) -> None:
        """Called from the preview timer thread with a BGR numpy array."""
        if bgr is None or bgr.size == 0:
            return
        h, w = bgr.shape[:2]
        rgb = bgr[..., ::-1].copy()            # BGR → RGB
        qi  = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        with self._lock:
            self._image = qi.copy()            # copy so the numpy buffer is safe to release

    def requestImage(self, _id: str, _size: QSize) -> tuple[QImage, QSize]:
        # PyQt6: the C++ QSize* output is represented by the second element of
        # the returned tuple; requestedSize is not forwarded to Python.
        with self._lock:
            img = self._image.copy()
        return img, img.size()
