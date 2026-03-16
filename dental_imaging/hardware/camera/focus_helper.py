"""
Helper functions for camera focus and image quality diagnostics.
"""

from typing import Dict, Optional
from dental_imaging.hardware.camera.basler_camera import BaslerCamera
from pypylon import pylon


def get_focus_settings(camera: BaslerCamera) -> Dict[str, any]:
    """
    Get focus-related settings if available.
    
    Args:
        camera: BaslerCamera instance
        
    Returns:
        Dictionary with focus settings
    """
    if not camera.is_connected or not camera.camera:
        return {}
    
    settings = {}
    
    try:
        cam = camera.camera
        
        # Check if focus is available (not all cameras support this)
        try:
            # Some Basler cameras have focus control
            if hasattr(cam, 'Focus'):
                settings["focus_available"] = True
                settings["focus_value"] = cam.Focus.GetValue()
            else:
                settings["focus_available"] = False
        except Exception:
            settings["focus_available"] = False
        
        # Get pixel format (affects image quality)
        try:
            settings["pixel_format"] = str(cam.PixelFormat.GetValue())
        except Exception:
            pass
        
        # Get actual image dimensions
        try:
            settings["width"] = cam.Width.GetValue()
            settings["height"] = cam.Height.GetValue()
        except Exception:
            pass
        
    except Exception:
        pass
    
    return settings


def diagnose_blur_issues(camera: BaslerCamera) -> list[str]:
    """
    Diagnose potential causes of blur in camera images.
    
    Args:
        camera: BaslerCamera instance
        
    Returns:
        List of potential issues and recommendations
    """
    issues = []
    
    if not camera.is_connected:
        return ["Camera not connected"]
    
    try:
        cam = camera.camera
        
        # Check exposure time (motion blur)
        try:
            exposure_auto = cam.ExposureAuto.GetValue()
            if exposure_auto != "Continuous":
                exposure_time = cam.ExposureTime.GetValue()
                if exposure_time > 100000:  # > 100ms
                    issues.append(f"Exposure time is very long ({exposure_time/1000:.1f}ms) - may cause motion blur")
        except Exception:
            pass
        
        # Check pixel format
        try:
            pixel_format = str(cam.PixelFormat.GetValue())
            if "Mono" in pixel_format:
                issues.append("Camera is in monochrome mode - ensure color mode if needed")
        except Exception:
            pass
        
        # Check resolution
        try:
            width = cam.Width.GetValue()
            height = cam.Height.GetValue()
            if width < 1000 or height < 1000:
                issues.append(f"Resolution is low ({width}x{height}) - may appear blurry")
        except Exception:
            pass
        
        # Check if focus is available
        focus_settings = get_focus_settings(camera)
        if not focus_settings.get("focus_available", False):
            issues.append("Camera focus control not available - check physical lens focus")
        
    except Exception:
        pass
    
    if not issues:
        issues.append("No obvious software issues detected - check physical lens focus")
    
    return issues
