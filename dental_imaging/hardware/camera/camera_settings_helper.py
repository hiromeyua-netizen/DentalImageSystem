"""
Helper functions for camera settings and diagnostics.
"""

from typing import Dict, Optional
from pypylon import pylon
from dental_imaging.hardware.camera.basler_camera import BaslerCamera


def get_camera_settings(camera: BaslerCamera) -> Dict[str, any]:
    """
    Get current camera settings for diagnostics.
    
    Args:
        camera: BaslerCamera instance
        
    Returns:
        Dictionary with current camera settings
    """
    if not camera.is_connected or not camera.camera:
        return {}
    
    settings = {}
    
    try:
        cam = camera.camera
        
        # Resolution
        try:
            settings["width"] = cam.Width.GetValue()
            settings["height"] = cam.Height.GetValue()
        except Exception:
            pass
        
        # Exposure
        try:
            settings["exposure_auto"] = cam.ExposureAuto.GetValue()
            if settings["exposure_auto"] != "Continuous":
                settings["exposure_time"] = cam.ExposureTime.GetValue()
            else:
                settings["exposure_time"] = "Auto"
        except Exception:
            pass
        
        # Gain
        try:
            settings["gain_auto"] = cam.GainAuto.GetValue()
            if settings["gain_auto"] != "Continuous":
                settings["gain"] = cam.Gain.GetValue()
            else:
                settings["gain"] = "Auto"
        except Exception:
            pass
        
        # Frame rate
        try:
            settings["frame_rate_enabled"] = cam.AcquisitionFrameRateEnable.GetValue()
            if settings["frame_rate_enabled"]:
                settings["frame_rate"] = cam.AcquisitionFrameRate.GetValue()
        except Exception:
            pass
        
        # Pixel format
        try:
            settings["pixel_format"] = str(cam.PixelFormat.GetValue())
        except Exception:
            pass
        
    except Exception:
        pass
    
    return settings


def print_camera_settings(camera: BaslerCamera) -> None:
    """
    Print current camera settings to console.
    
    Args:
        camera: BaslerCamera instance
    """
    settings = get_camera_settings(camera)
    
    if not settings:
        print("Could not retrieve camera settings")
        return
    
    print("\n" + "=" * 50)
    print("Current Camera Settings:")
    print("=" * 50)
    
    if "width" in settings and "height" in settings:
        print(f"Resolution: {settings['width']} x {settings['height']}")
    
    if "exposure_auto" in settings:
        print(f"Exposure Auto: {settings['exposure_auto']}")
        if "exposure_time" in settings:
            if settings["exposure_time"] == "Auto":
                print(f"Exposure Time: Auto")
            else:
                print(f"Exposure Time: {settings['exposure_time']:.1f} μs ({settings['exposure_time']/1000:.2f} ms)")
    
    if "gain_auto" in settings:
        print(f"Gain Auto: {settings['gain_auto']}")
        if "gain" in settings:
            if settings["gain"] == "Auto":
                print(f"Gain: Auto")
            else:
                print(f"Gain: {settings['gain']:.2f}")
    
    if "frame_rate" in settings:
        print(f"Frame Rate: {settings['frame_rate']:.1f} fps")
    
    if "pixel_format" in settings:
        print(f"Pixel Format: {settings['pixel_format']}")
    
    print("=" * 50 + "\n")
