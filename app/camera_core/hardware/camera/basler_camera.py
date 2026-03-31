"""
Basler camera wrapper class for camera operations.
"""

from typing import Optional, Tuple

import numpy as np
from pypylon import pylon

from camera_core.exceptions.camera_exceptions import (
    CameraConfigurationError,
    CameraConnectionError,
    CameraGrabError,
    CameraInitializationError,
    CameraNotFoundError,
)
from camera_core.hardware.camera import camera_detection
from camera_core.hardware.camera.camera_detection import CameraInfo
from camera_core.models.camera_config import CameraConfig
from camera_core.utils.frame_converter import grab_result_to_opencv, resize_for_preview


class BaslerCamera:
    """High-level interface for Basler preview and capture."""

    def __init__(self, camera_info: Optional[CameraInfo] = None):
        self.camera_info = camera_info
        self.camera: Optional[pylon.InstantCamera] = None
        self.is_connected = False
        self.is_grabbing = False
        self.config: Optional[CameraConfig] = None

    def connect(self, camera_info: Optional[CameraInfo] = None) -> None:
        if camera_info:
            self.camera_info = camera_info

        if not self.camera_info:
            self.camera_info = camera_detection.get_first_available_camera()

        if not self.camera_info:
            raise CameraNotFoundError("No camera available for connection")

        try:
            tl_factory = pylon.TlFactory.GetInstance()
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

            self.camera = pylon.InstantCamera(tl_factory.CreateDevice(device))
            self.camera.Open()
            self.is_connected = True

        except CameraNotFoundError:
            raise
        except Exception as e:
            raise CameraConnectionError(f"Failed to connect to camera: {str(e)}") from e

    def disconnect(self) -> None:
        if self.is_grabbing:
            self.stop_grabbing()

        if self.camera and self.is_connected:
            try:
                self.camera.Close()
            except Exception:
                pass
            finally:
                self.camera = None
                self.is_connected = False

    def configure(self, config: CameraConfig) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            self.camera.Width.SetValue(config.resolution.width)
            self.camera.Height.SetValue(config.resolution.height)

            if config.exposure.auto:
                self.camera.ExposureAuto.SetValue("Continuous")
            else:
                self.camera.ExposureAuto.SetValue("Off")
                self.camera.ExposureTime.SetValue(config.exposure.value)

            if config.gain.auto:
                self.camera.GainAuto.SetValue("Continuous")
            else:
                self.camera.GainAuto.SetValue("Off")
                self.camera.Gain.SetValue(config.gain.value)

            try:
                if config.white_balance.auto:
                    self.camera.BalanceWhiteAuto.SetValue("Continuous")
                else:
                    self.camera.BalanceWhiteAuto.SetValue("Off")
            except Exception:
                pass

            try:
                self.camera.AcquisitionFrameRateEnable.SetValue(True)
                self.camera.AcquisitionFrameRate.SetValue(config.frame_rate)
            except Exception:
                pass

            self.config = config

        except Exception as e:
            raise CameraConfigurationError(f"Failed to configure camera: {str(e)}") from e

    def start_grabbing(self) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        if self.is_grabbing:
            return

        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.is_grabbing = True
        except Exception as e:
            raise CameraInitializationError(f"Failed to start grabbing: {str(e)}") from e

    def stop_grabbing(self) -> None:
        if self.camera and self.is_grabbing:
            try:
                self.camera.StopGrabbing()
            except Exception:
                pass
            finally:
                self.is_grabbing = False

    def grab_frame(self, timeout_ms: int = 5000) -> Optional[np.ndarray]:
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
                    pass

    def grab_preview_frame(
        self, preview_width: int = 1920, preview_height: int = 1080
    ) -> Optional[np.ndarray]:
        frame = self.grab_frame()
        if frame is None:
            return None

        return resize_for_preview(frame, preview_width, preview_height)

    def set_exposure(self, exposure_time_us: int, auto: bool = False) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            if auto:
                self.camera.ExposureAuto.SetValue("Continuous")
            else:
                self.camera.ExposureAuto.SetValue("Off")
                self.camera.ExposureTime.SetValue(exposure_time_us)

            if self.config:
                self.config.exposure.auto = auto
                if not auto:
                    self.config.exposure.value = exposure_time_us

        except Exception as e:
            raise CameraConfigurationError(f"Failed to set exposure: {str(e)}") from e

    def set_gain(self, gain: float, auto: bool = False) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            if auto:
                self.camera.GainAuto.SetValue("Continuous")
            else:
                self.camera.GainAuto.SetValue("Off")
                self.camera.Gain.SetValue(gain)

            if self.config:
                self.config.gain.auto = auto
                if not auto:
                    self.config.gain.value = gain

        except Exception as e:
            raise CameraConfigurationError(f"Failed to set gain: {str(e)}") from e

    def get_exposure(self) -> Tuple[bool, int]:
        if not self.is_connected:
            return (False, 0)

        try:
            auto = self.camera.ExposureAuto.GetValue() == "Continuous"
            if auto:
                return (True, 0)
            exposure = int(self.camera.ExposureTime.GetValue())
            return (False, exposure)
        except Exception:
            return (False, 0)

    def get_gain(self) -> Tuple[bool, float]:
        if not self.is_connected:
            return (False, 0.0)

        try:
            auto = self.camera.GainAuto.GetValue() == "Continuous"
            if auto:
                return (True, 0.0)
            gain = float(self.camera.Gain.GetValue())
            return (False, gain)
        except Exception:
            return (False, 0.0)

    def set_white_balance(self, auto: bool = True) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            if auto:
                self.camera.BalanceWhiteAuto.SetValue("Continuous")
            else:
                self.camera.BalanceWhiteAuto.SetValue("Off")

            if self.config:
                self.config.white_balance.auto = auto

        except Exception as e:
            raise CameraConfigurationError(f"Failed to set white balance: {str(e)}") from e

    def get_white_balance(self) -> bool:
        if not self.is_connected:
            return False

        try:
            return self.camera.BalanceWhiteAuto.GetValue() == "Continuous"
        except Exception:
            return False

    def set_frame_rate(self, frame_rate: float) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            self.camera.AcquisitionFrameRateEnable.SetValue(True)
            self.camera.AcquisitionFrameRate.SetValue(frame_rate)

            if self.config:
                self.config.frame_rate = int(frame_rate)

        except Exception as e:
            raise CameraConfigurationError(f"Failed to set frame rate: {str(e)}") from e

    def get_frame_rate(self) -> float:
        if not self.is_connected:
            return 0.0

        try:
            if self.camera.AcquisitionFrameRateEnable.GetValue():
                return float(self.camera.AcquisitionFrameRate.GetValue())
            return 0.0
        except Exception:
            return 0.0

    def set_gamma(self, gamma: float) -> None:
        if not self.is_connected:
            raise CameraConnectionError("Camera not connected. Call connect() first.")

        try:
            self.camera.Gamma.SetValue(gamma)
        except Exception as e:
            raise CameraConfigurationError(f"Failed to set gamma: {str(e)}") from e

    def get_gamma(self) -> Optional[float]:
        if not self.is_connected:
            return None

        try:
            return float(self.camera.Gamma.GetValue())
        except Exception:
            return None

    def __enter__(self):
        if not self.is_connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __del__(self):
        self.disconnect()
