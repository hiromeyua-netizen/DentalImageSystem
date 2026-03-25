"""Preview pipeline: zoom+pan crop, then flip/rotate. Pan uses 0–1 along free axis (0=left/top … 1=right/bottom)."""
from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def zoom_crop_pan(
    bgr: Optional[np.ndarray],
    pct: int,
    pan_x: float,
    pan_y: float,
) -> Tuple[Optional[np.ndarray], int, int, int, int, int, int]:
    """
    Crop window for zoom with pannable origin.

    Returns ``(cropped_bgr|None, x0, y0, cw, ch, fw, fh)`` in source pixel coords.
    When ``pct <= 2``, returns the full frame and (0,0,fw,fh,fw,fh).
    ``pan_x`` / ``pan_y`` in [0,1]: 0.5 = centred; 0 = crop hugging left / top edge.
    """
    if bgr is None or bgr.size == 0:
        return None, 0, 0, 0, 0, 0, 0
    fh, fw = bgr.shape[:2]
    if pct <= 2:
        return bgr, 0, 0, fw, fh, fw, fh

    t = pct / 100.0
    cw = max(32, int(fw * (1.0 - 0.7 * t)))
    ch = max(32, int(fh * (1.0 - 0.7 * t)))
    cw = min(cw, fw)
    ch = min(ch, fh)
    max_x0 = max(0, fw - cw)
    max_y0 = max(0, fh - ch)

    px = max(0.0, min(1.0, float(pan_x)))
    py = max(0.0, min(1.0, float(pan_y)))
    x0 = int(round(px * max_x0)) if max_x0 > 0 else 0
    y0 = int(round(py * max_y0)) if max_y0 > 0 else 0

    cropped = bgr[y0 : y0 + ch, x0 : x0 + cw].copy()
    return cropped, x0, y0, cw, ch, fw, fh


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
