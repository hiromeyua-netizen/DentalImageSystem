"""Preview pipeline helpers. Order matches ``MainWindow._apply_view_transforms``: zoom crop, then flip/rotate."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


def zoom_crop(bgr: Optional[np.ndarray], pct: int) -> Optional[np.ndarray]:
    """
    Centre crop then (implicitly via display) scale up — ``pct`` is 0–100 “zoom level”
    like the bottom bar (higher = tighter crop / more “magnified”).
    """
    if bgr is None or bgr.size == 0:
        return bgr
    if pct <= 2:
        return bgr
    fh, fw = bgr.shape[:2]
    t = pct / 100.0
    cw = max(32, int(fw * (1.0 - 0.7 * t)))
    ch = max(32, int(fh * (1.0 - 0.7 * t)))
    cw = min(cw, fw)
    ch = min(ch, fh)
    x0 = (fw - cw) // 2
    y0 = (fh - ch) // 2
    return bgr[y0 : y0 + ch, x0 : x0 + cw].copy()


def apply_view_transforms(
    bgr: Optional[np.ndarray],
    *,
    flip_h: bool,
    flip_v: bool,
    rotate_q: int,
) -> Optional[np.ndarray]:
    if bgr is None or bgr.size == 0:
        return bgr
    out = bgr
    if flip_h:
        out = cv2.flip(out, 1)
    if flip_v:
        out = cv2.flip(out, 0)
    for _ in range(int(rotate_q) % 4):
        out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
    return out
