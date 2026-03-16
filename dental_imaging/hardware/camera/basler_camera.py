"""
Basler camera wrapper class for camera operations.
"""

from typing import Optional
import numpy as np
from pypylon import pylon
from dental_imaging.hardware.camera.camera_detection import CameraInfo
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.utils.frame_converter import (
    grab_result_to_opencv,
    resize_for_preview
)
from dental_imaging.exceptions.camera_exceptions import (
    CameraNotFoundError,
    CameraConnectionError,
    CameraInitializationError,
    CameraConfigurationError,
    CameraDisconnectedError,
    CameraGrabError,
)


class BaslerCamera:
    """
    Wrapper class for Basler camera operations.
    
    This class provides a high-level interface for camera operations
    including initialization, configuration, preview, and capture.
    """
    
    def __init__(self, camera_info: Optional[CameraInfo] = None):
        """
        Initialize Basler camera.
        
        Args:
            camera_info: CameraInfo object. If None, uses first available camera.
            
        Raises:
            CameraNotFoundError: If no camera is available
            CameraConnectionError: If connection fails
        """
        self.camera_info = camera_info
        self.camera: Optional[pylon.InstantCamera] = None
        self.is_connected = False
        self.is_grabbing = False
        self.config: Optional[CameraConfig] = None
        
    def connect(self, camera_info: Optional[CameraInfo] = None) -> None:
        """
        Connect to the camera.
        
        Args:
            camera_info: CameraInfo object. If None, uses first available camera.
            
        Raises:
            CameraNotFoundError: If no camera is available
            CameraConnectionError: If connection fails
        """
        if camera_info:
            self.camera_info = camera_info
        
        if not self.camera_info:
            from dental_imaging.hardware.camera.camera_detection import get_first_available_camera
            self.camera_info = get_first_available_camera()
            
        if not self.camera_info:
            raise CameraNotFoundError("No camera available for connection")
        
        try:
            # Create camera instance
            tl_factory = pylon.TlFactory.GetInstance()
            
            # Create device from camera info
            devices = tl_factory.EnumerateDevices()
            device = None
            for dev in devices:
                if dev.GetSerialNumber() == self.camera_info.serial_number:
                    device = dev
                    break
            
            if not device:
                raise CameraNotFoundError(
                    f"Camera with serial {self.camera_info.serial_number} not found"
                )
            
            # Create and attach camera
            self.camera = pylon.InstantCamera(tl_factory.CreateDevice(device))
            self.camera.Open()
            self.is_connected = True
            
        except CameraNotFoundError:
            raise
        except Exception as e:
            raise CameraConnectionError(f"Failed to connect to camera: {str(e)}") from e
    
    def disconnect(self) -> None:
        """Disconnect from the camera."""
        if self.is_grabbing:
            self.stop_grabbing()
        
        if self.camera and self.is_connected:
            try:
                self.camera.Close()
            except Exception:
                pass  # Ignore errors during disconnect
            finally:
                self.camera = None
                self.is_connected = False
    
    def configure(self, config: CameraConfig) -> None:
        """
        Configure camera with settings.
        
        Args:
            config: CameraConfig object with camera settings
            
        Raises:
            CameraConfigurationError: If configuration fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            # Set resolution
            self.camera.Width.SetValue(config.resolution.width)
            self.camera.Height.SetValue(config.resolution.height)
            
            # Set exposure
            if config.exposure.auto:
                self.camera.ExposureAuto.SetValue("Continuous")
            else:
                self.camera.ExposureAuto.SetValue("Off")
                self.camera.ExposureTime.SetValue(config.exposure.value)
            
            # Set gain
            if config.gain.auto:
                self.camera.GainAuto.SetValue("Continuous")
            else:
                self.camera.GainAuto.SetValue("Off")
                self.camera.Gain.SetValue(config.gain.value)
            
            # Set white balance (if supported)
            try:
                if config.white_balance.auto:
                    self.camera.BalanceWhiteAuto.SetValue("Continuous")
                else:
                    self.camera.BalanceWhiteAuto.SetValue("Off")
            except Exception:
                # White balance not supported on all cameras
                pass
            
            # Set frame rate
            try:
                self.camera.AcquisitionFrameRateEnable.SetValue(True)
                self.camera.AcquisitionFrameRate.SetValue(config.frame_rate)
            except Exception:
                # Frame rate control not supported on all cameras
                pass
            
            self.config = config
            
        except Exception as e:
            raise CameraConfigurationError(f"Failed to configure camera: {str(e)}") from e
    
    def start_grabbing(self) -> None:
        """
        Start continuous image grabbing.
        
        Raises:
            CameraConnectionError: If camera is not connected
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        if self.is_grabbing:
            return  # Already grabbing
        
        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.is_grabbing = True
        except Exception as e:
            raise CameraInitializationError(f"Failed to start grabbing: {str(e)}") from e
    
    def stop_grabbing(self) -> None:
        """Stop continuous image grabbing."""
        if self.camera and self.is_grabbing:
            try:
                self.camera.StopGrabbing()
            except Exception:
                pass  # Ignore errors
            finally:
                self.is_grabbing = False
    
    def grab_frame(self, timeout_ms: int = 5000) -> Optional[np.ndarray]:
        """
        Grab a single frame.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            numpy array (BGR format) or None if grab failed
            
        Raises:
            CameraGrabError: If grab fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            if not self.is_grabbing:
                # Grab single frame without continuous grabbing
                grab_result = self.camera.GrabOne(timeout_ms)
            else:
                # Retrieve latest frame from continuous grabbing
                grab_result = self.camera.RetrieveResult(timeout_ms, pylon.TimeoutHandling_ThrowException)
            
            if not grab_result.GrabSucceeded():
                return None
            
            # Convert to OpenCV format
            img = grab_result_to_opencv(grab_result)
            
            return img
            
        except pylon.TimeoutException:
            raise CameraGrabError(f"Frame grab timeout after {timeout_ms}ms")
        except Exception as e:
            raise CameraGrabError(f"Failed to grab frame: {str(e)}") from e
    
    def grab_preview_frame(self, preview_width: int = 1920, preview_height: int = 1080) -> Optional[np.ndarray]:
        """
        Grab a frame and resize it for preview.
        
        Args:
            preview_width: Target preview width
            preview_height: Target preview height
            
        Returns:
            Resized numpy array for preview or None if grab failed
        """
        frame = self.grab_frame()
        if frame is None:
            return None
        
        return resize_for_preview(frame, preview_width, preview_height)
    
    def set_exposure(self, exposure_time_us: int, auto: bool = False) -> None:
        """
        Set camera exposure time.
        
        Args:
            exposure_time_us: Exposure time in microseconds
            auto: If True, enable auto-exposure
            
        Raises:
            CameraConnectionError: If camera is not connected
            CameraConfigurationError: If setting fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            if auto:
                self.camera.ExposureAuto.SetValue("Continuous")
            else:
                self.camera.ExposureAuto.SetValue("Off")
                self.camera.ExposureTime.SetValue(exposure_time_us)
                
                # Update config if exists
                if self.config:
                    self.config.exposure.auto = auto
                    self.config.exposure.value = exposure_time_us
        except Exception as e:
            raise CameraConfigurationError(f"Failed to set exposure: {str(e)}") from e
    
    def set_gain(self, gain: float, auto: bool = False) -> None:
        """
        Set camera gain.
        
        Args:
            gain: Gain value
            auto: If True, enable auto-gain
            
        Raises:
            CameraConnectionError: If camera is not connected
            CameraConfigurationError: If setting fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            if auto:
                self.camera.GainAuto.SetValue("Continuous")
            else:
                self.camera.GainAuto.SetValue("Off")
                self.camera.Gain.SetValue(gain)
                
                # Update config if exists
                if self.config:
                    self.config.gain.auto = auto
                    self.config.gain.value = gain
        except Exception as e:
            raise CameraConfigurationError(f"Failed to set gain: {str(e)}") from e
    
    def get_exposure_range(self) -> tuple:
        """
        Get minimum and maximum exposure time values.
        
        Returns:
            Tuple of (min_exposure, max_exposure) in microseconds
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            min_exp = self.camera.ExposureTime.GetMin()
            max_exp = self.camera.ExposureTime.GetMax()
            return (min_exp, max_exp)
        except Exception:
            return (1000, 1000000)  # Default range if not available
    
    def get_gain_range(self) -> tuple:
        """
        Get minimum and maximum gain values.
        
        Returns:
            Tuple of (min_gain, max_gain)
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            min_gain = self.camera.Gain.GetMin()
            max_gain = self.camera.Gain.GetMax()
            return (min_gain, max_gain)
        except Exception:
            return (0.0, 48.0)  # Default range if not available
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
