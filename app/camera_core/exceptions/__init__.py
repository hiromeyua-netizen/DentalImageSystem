"""Custom exception classes."""

from camera_core.exceptions.camera_exceptions import (
    CameraConfigurationError,
    CameraConnectionError,
    CameraDisconnectedError,
    CameraException,
    CameraGrabError,
    CameraInitializationError,
    CameraNotFoundError,
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
