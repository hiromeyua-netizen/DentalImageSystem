"""Camera module for Basler camera integration."""

from dental_imaging.hardware.camera.camera_detection import (
    detect_cameras,
    find_camera_by_serial,
    get_first_available_camera,
    get_camera_count,
    CameraInfo,
)
from dental_imaging.hardware.camera.basler_camera import BaslerCamera

__all__ = [
    "detect_cameras",
    "find_camera_by_serial",
    "get_first_available_camera",
    "get_camera_count",
    "CameraInfo",
    "BaslerCamera",
]
