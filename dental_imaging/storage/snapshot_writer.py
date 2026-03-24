"""
Phase 1: persist full-resolution captures to disk.

A small, dependency-free writer. Phase 5 can replace this with a storage manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class SnapshotWriteResult:
    """Outcome of a snapshot write operation."""

    path: Path
    width: int
    height: int


class SnapshotWriter:
    """
    Save BGR ``numpy`` frames under a base directory with timestamped names.

    Thread-safety: use from the main / camera thread only unless externally synchronized.
    """

    def __init__(
        self,
        base_directory: Path,
        image_format: str = "png",
        jpeg_quality: int = 94,
    ) -> None:
        fmt = (image_format or "png").lower()
        if fmt == "jpeg":
            fmt = "jpg"
        self._format = fmt
        self._jpeg_quality = max(1, min(100, int(jpeg_quality)))
        self._base = Path(base_directory)

    @property
    def base_directory(self) -> Path:
        return self._base

    @property
    def image_format(self) -> str:
        return self._format

    def set_image_format(self, image_format: str) -> None:
        fmt = (image_format or "png").lower()
        if fmt == "jpeg":
            fmt = "jpg"
        self._format = fmt

    def set_jpeg_quality(self, quality: int) -> None:
        self._jpeg_quality = max(1, min(100, int(quality)))

    @property
    def jpeg_quality(self) -> int:
        return self._jpeg_quality

    def save_bgr(
        self,
        image: np.ndarray,
        prefix: str = "capture",
    ) -> SnapshotWriteResult:
        """
        Write ``image`` (BGR, uint8 or convertible) to disk.

        Raises:
            ValueError: If the array is empty or not 2D/3D.
            RuntimeError: If OpenCV fails to write the file.
        """
        if image is None or image.size == 0:
            raise ValueError("Cannot save empty image")

        if image.ndim not in (2, 3):
            raise ValueError("Image must be 2D (mono) or 3D (multi-channel)")

        h, w = int(image.shape[0]), int(image.shape[1])
        self._base.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)
        if not safe_prefix:
            safe_prefix = "capture"

        ext = self._format if self._format != "jpeg" else "jpg"
        path = self._base / f"{safe_prefix}_{stamp}.{ext}"

        params = self._encode_params()
        ok = cv2.imwrite(str(path), image, params)
        if not ok:
            raise RuntimeError(f"Failed to write image: {path}")

        return SnapshotWriteResult(path=path, width=w, height=h)

    def _encode_params(self) -> list[int]:
        if self._format in ("jpg", "jpeg"):
            return [int(cv2.IMWRITE_JPEG_QUALITY), self._jpeg_quality]
        if self._format in ("png",):
            return [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
        return []
