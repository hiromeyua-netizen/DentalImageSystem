"""
FrameProvider — QQuickImageProvider that serves camera frames to QML.
Routes ``frame`` vs ``overview`` id for main preview vs zoom minimap.
"""
import threading

import cv2
import numpy as np
from PyQt6.QtGui import QImage
from PyQt6.QtQuick import QQuickImageProvider


class FrameProvider(QQuickImageProvider):
    W, H = 1920, 1080
    OVERVIEW_MAX_W = 200

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock = threading.Lock()
        self._frame = self._placeholder()
        self._overview = self._placeholder_overview()

    def update_frame(self, bgr_array):
        if bgr_array is None or bgr_array.size == 0:
            return
        h, w = bgr_array.shape[:2]
        rgb = bgr_array[..., ::-1].copy()
        qi = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        with self._lock:
            self._frame = qi.copy()

    def update_overview(self, bgr_array):
        """Downscaled full-frame thumbnail for minimap (before zoom crop)."""
        if bgr_array is None or bgr_array.size == 0:
            return
        h, w = bgr_array.shape[:2]
        tw = min(self.OVERVIEW_MAX_W, max(1, w))
        th = max(1, int(round(h * tw / w)))
        small = cv2.resize(bgr_array, (tw, th), interpolation=cv2.INTER_AREA)
        rgb = small[..., ::-1].copy()
        qi = QImage(rgb.data, tw, th, tw * 3, QImage.Format.Format_RGB888)
        with self._lock:
            self._overview = qi.copy()

    def reset_to_placeholder(self):
        with self._lock:
            self._frame = self._placeholder()
            self._overview = self._placeholder_overview()

    def requestImage(self, id_str, _size):
        key = (id_str or "frame").split("?")[0].lower()
        with self._lock:
            img = self._overview.copy() if key == "overview" else self._frame.copy()
        return img, img.size()

    @classmethod
    def _placeholder(cls):
        a = np.empty((cls.H, cls.W, 3), dtype=np.uint8)
        for y in range(cls.H):
            t = y / cls.H
            a[y] = (int(20 - 4 * t), int(22 - 4 * t), int(30 - 6 * t))
        qi = QImage(a.data, cls.W, cls.H, cls.W * 3, QImage.Format.Format_RGB888)
        return qi.copy()

    @classmethod
    def _placeholder_overview(cls):
        tw = cls.OVERVIEW_MAX_W
        th = max(1, int(round(cls.H * tw / cls.W)))
        a = np.empty((th, tw, 3), dtype=np.uint8)
        a[:] = (24, 26, 34)
        qi = QImage(a.data, tw, th, tw * 3, QImage.Format.Format_RGB888)
        return qi.copy()
