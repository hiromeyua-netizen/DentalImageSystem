"""Preview / view transforms: flip + 90° steps. Order matches ``main_window._apply_view_transforms``."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


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
