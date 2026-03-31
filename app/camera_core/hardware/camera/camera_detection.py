"""
Camera detection and discovery functionality for Basler cameras.
"""

from typing import Dict, List, Optional

from pypylon import pylon

from camera_core.exceptions.camera_exceptions import CameraException


class CameraInfo:
    """Information about a detected camera."""

    def __init__(self, device_info: pylon.DeviceInfo):
        self.serial_number = device_info.GetSerialNumber()
        self.model_name = device_info.GetModelName()
        self.vendor_name = device_info.GetVendorName()
        self.user_defined_name = device_info.GetUserDefinedName()
        self.device_class = device_info.GetDeviceClass()
        self.full_name = device_info.GetFullName()
        self.friendly_name = device_info.GetFriendlyName()

    def __repr__(self) -> str:
        return (
            f"CameraInfo(serial={self.serial_number}, "
            f"model={self.model_name}, "
            f"vendor={self.vendor_name})"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "serial_number": self.serial_number,
            "model_name": self.model_name,
            "vendor_name": self.vendor_name,
            "user_defined_name": self.user_defined_name,
            "device_class": self.device_class,
            "full_name": self.full_name,
            "friendly_name": self.friendly_name,
        }


def detect_cameras() -> List[CameraInfo]:
    """Detect all available Basler cameras."""
    try:
        tl_factory = pylon.TlFactory.GetInstance()
        devices = tl_factory.EnumerateDevices()

        if not devices:
            return []

        return [CameraInfo(device) for device in devices]

    except Exception as e:
        raise CameraException(f"Failed to detect cameras: {str(e)}") from e


def find_camera_by_serial(serial_number: str) -> Optional[CameraInfo]:
    """Find a camera by its serial number."""
    for camera in detect_cameras():
        if camera.serial_number == serial_number:
            return camera
    return None


def get_first_available_camera() -> Optional[CameraInfo]:
    """Get the first available camera."""
    cameras = detect_cameras()
    if cameras:
        return cameras[0]
    return None


def get_camera_count() -> int:
    """Get the number of available cameras."""
    try:
        return len(detect_cameras())
    except CameraException:
        return 0
