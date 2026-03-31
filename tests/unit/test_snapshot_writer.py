"""Tests for Phase 1 snapshot writer."""

import numpy as np
import pytest

from camera_core.storage.snapshot_writer import SnapshotWriter


def test_save_bgr_png(tmp_path) -> None:
    w = SnapshotWriter(tmp_path, "png")
    img = np.zeros((64, 48, 3), dtype=np.uint8)
    img[:, :, 1] = 200
    result = w.save_bgr(img, prefix="test")
    assert result.path.is_file()
    assert result.width == 48 and result.height == 64
    assert result.path.suffix == ".png"


def test_save_bgr_empty_raises(tmp_path) -> None:
    w = SnapshotWriter(tmp_path, "png")
    with pytest.raises(ValueError, match="empty"):
        w.save_bgr(np.array([]))
