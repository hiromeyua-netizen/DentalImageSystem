"""
Basler camera wrapper class for camera operations.
"""

from typing import Optional, Tuple
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
        
        grab_result = None
        try:
            if not self.is_grabbing:
                grab_result = self.camera.GrabOne(timeout_ms)
            else:
                grab_result = self.camera.RetrieveResult(
                    timeout_ms, pylon.TimeoutHandling_ThrowException
                )

            if grab_result is None:
                return None

            if not grab_result.GrabSucceeded():
                return None

            return grab_result_to_opencv(grab_result)

        except pylon.TimeoutException:
            raise CameraGrabError(f"Frame grab timeout after {timeout_ms}ms")
        except Exception as e:
            raise CameraGrabError(f"Failed to grab frame: {str(e)}") from e
        finally:
            if grab_result is not None:
                grab_result.Release()

    def grab_still_frame(self, timeout_ms: int = 5000) -> Optional[np.ndarray]:
        """
        Capture one full-resolution frame using ``GrabOne``.

        If live preview is running (continuous grab), acquisition is stopped for
        this shot and then restarted. This avoids ``RetrieveResult`` / NULL
        ``GrabResultPtr`` issues seen with ``GrabStrategy_LatestImageOnly`` on
        some Basler models when taking a still while streaming.
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        was_grabbing = self.is_grabbing
        if was_grabbing:
            self.stop_grabbing()

        grab_result = None
        try:
            grab_result = self.camera.GrabOne(timeout_ms)
            if grab_result is None:
                return None
            if not grab_result.GrabSucceeded():
                return None
            return grab_result_to_opencv(grab_result)
        except pylon.TimeoutException:
            raise CameraGrabError(f"Frame grab timeout after {timeout_ms}ms")
        except Exception as e:
            raise CameraGrabError(f"Failed to grab frame: {str(e)}") from e
        finally:
            if grab_result is not None:
                grab_result.Release()
            if was_grabbing:
                try:
                    self.start_grabbing()
                except Exception:
                    # Do not mask a successful GrabOne/exception above; user can press Start Preview.
                    pass

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
        Set exposure time in real-time.
        
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
                if not auto:
                    self.config.exposure.value = exposure_time_us
                    
        except Exception as e:
            raise CameraConfigurationError(f"Failed to set exposure: {str(e)}") from e
    
    def set_gain(self, gain: float, auto: bool = False) -> None:
        """
        Set gain in real-time.
        
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
                if not auto:
                    self.config.gain.value = gain
                    
        except Exception as e:
            raise CameraConfigurationError(f"Failed to set gain: {str(e)}") from e
    
    def get_exposure(self) -> Tuple[bool, int]:
        """
        Get current exposure settings.
        
        Returns:
            Tuple of (is_auto, exposure_time_us)
        """
        if not self.is_connected:
            return (False, 0)
        
        try:
            auto = self.camera.ExposureAuto.GetValue() == "Continuous"
            if auto:
                return (True, 0)
            else:
                exposure = int(self.camera.ExposureTime.GetValue())
                return (False, exposure)
        except Exception:
            return (False, 0)
    
    def get_gain(self) -> Tuple[bool, float]:
        """
        Get current gain settings.
        
        Returns:
            Tuple of (is_auto, gain_value)
        """
        if not self.is_connected:
            return (False, 0.0)
        
        try:
            auto = self.camera.GainAuto.GetValue() == "Continuous"
            if auto:
                return (True, 0.0)
            else:
                gain = float(self.camera.Gain.GetValue())
                return (False, gain)
        except Exception:
            return (False, 0.0)
    
    def set_white_balance(self, auto: bool = True) -> None:
        """
        Set white balance mode.
        
        Args:
            auto: If True, enable auto white balance
            
        Raises:
            CameraConnectionError: If camera is not connected
            CameraConfigurationError: If setting fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            if auto:
                self.camera.BalanceWhiteAuto.SetValue("Continuous")
            else:
                self.camera.BalanceWhiteAuto.SetValue("Off")
            
            # Update config if exists
            if self.config:
                self.config.white_balance.auto = auto
                
        except Exception as e:
            # White balance not supported on all cameras
            raise CameraConfigurationError(f"Failed to set white balance: {str(e)}") from e
    
    def get_white_balance(self) -> bool:
        """
        Get current white balance mode.
        
        Returns:
            True if auto white balance is enabled, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            return self.camera.BalanceWhiteAuto.GetValue() == "Continuous"
        except Exception:
            return False
    
    def set_frame_rate(self, frame_rate: float) -> None:
        """
        Set frame rate.
        
        Args:
            frame_rate: Target frame rate in fps
            
        Raises:
            CameraConnectionError: If camera is not connected
            CameraConfigurationError: If setting fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            self.camera.AcquisitionFrameRateEnable.SetValue(True)
            self.camera.AcquisitionFrameRate.SetValue(frame_rate)
            
            # Update config if exists
            if self.config:
                self.config.frame_rate = int(frame_rate)
                
        except Exception as e:
            # Frame rate control not supported on all cameras
            raise CameraConfigurationError(f"Failed to set frame rate: {str(e)}") from e
    
    def get_frame_rate(self) -> float:
        """
        Get current frame rate.
        
        Returns:
            Current frame rate in fps, or 0 if not available
        """
        if not self.is_connected:
            return 0.0
        
        try:
            if self.camera.AcquisitionFrameRateEnable.GetValue():
                return float(self.camera.AcquisitionFrameRate.GetValue())
            return 0.0
        except Exception:
            return 0.0
    
    def set_gamma(self, gamma: float) -> None:
        """
        Set gamma correction value.
        
        Args:
            gamma: Gamma value (typically 0.5 to 3.0)
            
        Raises:
            CameraConnectionError: If camera is not connected
            CameraConfigurationError: If setting fails
        """
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")
        
        try:
            self.camera.Gamma.SetValue(gamma)
        except Exception as e:
            # Gamma not supported on all cameras
            raise CameraConfigurationError(f"Failed to set gamma: {str(e)}") from e
    
    def get_gamma(self) -> Optional[float]:
        """
        Get current gamma value.
        
        Returns:
            Current gamma value, or None if not available
        """
        if not self.is_connected:
            return None
        
        try:
            return float(self.camera.Gamma.GetValue())
        except Exception:
            return None
    
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
