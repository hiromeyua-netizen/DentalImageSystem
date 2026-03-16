"""
Camera detection and discovery functionality for Basler cameras.
"""

from typing import List, Optional, Dict
from pypylon import pylon
from dental_imaging.exceptions.camera_exceptions import (
    CameraNotFoundError,
    CameraException
)


class CameraInfo:
    """Information about a detected camera."""
    
    def __init__(self, device_info: pylon.DeviceInfo):
        """
        Initialize camera information from pylon DeviceInfo.
        
        Args:
            device_info: pylon DeviceInfo object
        """
        self.serial_number = device_info.GetSerialNumber()
        self.model_name = device_info.GetModelName()
        self.vendor_name = device_info.GetVendorName()
        self.user_defined_name = device_info.GetUserDefinedName()
        self.device_class = device_info.GetDeviceClass()
        self.full_name = device_info.GetFullName()
        self.friendly_name = device_info.GetFriendlyName()
        
    def __repr__(self) -> str:
        """String representation of camera info."""
        return (
            f"CameraInfo(serial={self.serial_number}, "
            f"model={self.model_name}, "
            f"vendor={self.vendor_name})"
        )
    
    def to_dict(self) -> Dict[str, str]:
        """Convert camera info to dictionary."""
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
    """
    Detect all available Basler cameras.
    
    Returns:
        List of CameraInfo objects for each detected camera.
        
    Raises:
        CameraException: If camera system initialization fails.
    """
    try:
        # Get the transport layer factory
        tl_factory = pylon.TlFactory.GetInstance()
        
        # Get all available devices
        devices = tl_factory.EnumerateDevices()
        
        if not devices:
            return []
        
        # Convert to CameraInfo objects
        camera_list = [CameraInfo(device) for device in devices]
        
        return camera_list
        
    except Exception as e:
        raise CameraException(f"Failed to detect cameras: {str(e)}") from e


def find_camera_by_serial(serial_number: str) -> Optional[CameraInfo]:
    """
    Find a camera by its serial number.
    
    Args:
        serial_number: Serial number of the camera to find.
        
    Returns:
        CameraInfo if found, None otherwise.
    """
    cameras = detect_cameras()
    
    for camera in cameras:
        if camera.serial_number == serial_number:
            return camera
    
    return None


def get_first_available_camera() -> Optional[CameraInfo]:
    """
    Get the first available camera.
    
    Returns:
        CameraInfo of the first camera, or None if no cameras found.
    """
    cameras = detect_cameras()
    
    if cameras:
        return cameras[0]
    
    return None


def get_camera_count() -> int:
    """
    Get the number of available cameras.
    
    Returns:
        Number of detected cameras.
    """
    try:
        cameras = detect_cameras()
        return len(cameras)
    except CameraException:
        return 0
