"""
FrameProvider — QQuickImageProvider that serves camera frames to QML.
Shows a dark placeholder until update_frame() is called from the camera thread.
"""
import threading, numpy as np
from PyQt6.QtCore import QSize
from PyQt6.QtGui  import QImage
from PyQt6.QtQuick import QQuickImageProvider


class FrameProvider(QQuickImageProvider):
    W, H = 1920, 1080

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock  = threading.Lock()
        self._frame = self._placeholder()

    def update_frame(self, bgr_array):
        if bgr_array is None or bgr_array.size == 0:
            return
        h, w = bgr_array.shape[:2]
        rgb = bgr_array[..., ::-1].copy()
        qi  = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        with self._lock:
            self._frame = qi.copy()

    def reset_to_placeholder(self):
        with self._lock:
            self._frame = self._placeholder()

    def requestImage(self, _id, _size):
        with self._lock:
            img = self._frame.copy()
        return img, img.size()

    @classmethod
    def _placeholder(cls):
        a = np.empty((cls.H, cls.W, 3), dtype=np.uint8)
        for y in range(cls.H):
            t = y / cls.H
            a[y] = (int(20 - 4*t), int(22 - 4*t), int(30 - 6*t))
        qi = QImage(a.data, cls.W, cls.H, cls.W * 3, QImage.Format.Format_RGB888)
        return qi.copy()
