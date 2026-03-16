"""Custom exception classes."""

from dental_imaging.exceptions.camera_exceptions import (
    CameraException,
    CameraNotFoundError,
    CameraConnectionError,
    CameraInitializationError,
    CameraDisconnectedError,
    CameraConfigurationError,
    CameraGrabError,
)

__all__ = [
    "CameraException",
    "CameraNotFoundError",
    "CameraConnectionError",
    "CameraInitializationError",
    "CameraDisconnectedError",
    "CameraConfigurationError",
    "CameraGrabError",
]
