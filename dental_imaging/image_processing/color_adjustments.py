"""
Software-side image adjustments (preview and capture) driven by Image Settings sliders.

Exposure and gain are applied on the camera in the UI layer; this module handles
White Balance, Contrast, Saturation, Warmth, and Tint as post-processing on BGR frames.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ImageSettingsPercent:
    """Slider values 0–100; 50 is neutral for all channels."""

    exposure: int = 50
    gain: int = 50
    white_balance: int = 50
    contrast: int = 50
    saturation: int = 50
    warmth: int = 50
    tint: int = 50


def _clamp_pct(v: int) -> int:
    return max(0, min(100, int(v)))


def apply_software_image_adjustments(
    bgr: np.ndarray,
    settings: ImageSettingsPercent,
) -> np.ndarray:
    """
    Apply white balance / warmth / tint / contrast / saturation in BGR space.

    Neutral at 50 for each software control; no-op when all software sliders are 50.
    """
    if bgr is None or bgr.size == 0:
        return bgr

    wb = _clamp_pct(settings.white_balance)
    c = _clamp_pct(settings.contrast)
    sat = _clamp_pct(settings.saturation)
    w = _clamp_pct(settings.warmth)
    t = _clamp_pct(settings.tint)

    if wb == c == sat == w == t == 50:
        return bgr

    out = bgr.astype(np.float32)

    # White balance: cooler (low) boosts B, reduces R; warmer (high) the opposite
    wb_k = (wb - 50) / 50.0
    out[:, :, 2] *= 1.0 + 0.35 * wb_k  # R
    out[:, :, 0] *= 1.0 - 0.35 * wb_k  # B

    # Warmth: yellow–blue (additive on R/B)
    wm = (w - 50) / 50.0
    out[:, :, 2] *= 1.0 + 0.25 * wm
    out[:, :, 0] *= 1.0 - 0.25 * wm

    # Tint: green ↔ magenta via green channel vs R/B
    tm = (t - 50) / 50.0
    out[:, :, 1] *= 1.0 + 0.22 * tm  # G

    out = np.clip(out, 0.0, 255.0)

    # Contrast around midpoint 128
    alpha = float(2.0 ** ((c - 50) / 35.0))
    beta = 128.0 * (1.0 - alpha)
    out = cv2.convertScaleAbs(out, alpha=alpha, beta=beta)

    # Saturation in HSV
    sm = float(2.0 ** ((sat - 50) / 40.0))
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sm, 0.0, 255.0)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return out
