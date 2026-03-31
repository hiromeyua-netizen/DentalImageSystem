"""Tests for software image adjustments."""

import numpy as np

from camera_core.image_processing.color_adjustments import (
    ImageSettingsPercent,
    apply_software_image_adjustments,
)


def test_neutral_is_noop() -> None:
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[:, :, :] = (40, 80, 120)
    out = apply_software_image_adjustments(img, ImageSettingsPercent())
    assert np.array_equal(out, img)


def test_saturation_changes() -> None:
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    img[:, :, 0] = 200
    img[:, :, 1] = 100
    img[:, :, 2] = 50
    s = ImageSettingsPercent(saturation=80)
    out = apply_software_image_adjustments(img, s)
    assert not np.array_equal(out, img)
