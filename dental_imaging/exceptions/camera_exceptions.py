"""
Camera-related exception classes.
"""


class CameraException(Exception):
    """Base exception for all camera-related errors."""
    pass


class CameraNotFoundError(CameraException):
    """Raised when no camera is detected or camera is not found."""
    pass


class CameraConnectionError(CameraException):
    """Raised when camera connection fails."""
    pass


class CameraInitializationError(CameraException):
    """Raised when camera initialization fails."""
    pass


class CameraDisconnectedError(CameraException):
    """Raised when camera disconnects during operation."""
    pass


class CameraConfigurationError(CameraException):
    """Raised when camera configuration fails."""
    pass


class CameraGrabError(CameraException):
    """Raised when image grab/retrieval fails."""
    pass
