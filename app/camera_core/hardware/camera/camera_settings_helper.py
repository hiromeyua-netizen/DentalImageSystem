"""
Helper functions for camera settings and diagnostics.
"""

from typing import Any, Dict

from camera_core.hardware.camera.basler_camera import BaslerCamera


def get_camera_settings(camera: BaslerCamera) -> Dict[str, Any]:
    """Get current camera settings for diagnostics."""
    if not camera.is_connected or not camera.camera:
        return {}

    settings: Dict[str, Any] = {}

    try:
        cam = camera.camera

        try:
            settings["width"] = cam.Width.GetValue()
            settings["height"] = cam.Height.GetValue()
        except Exception:
            pass

        try:
            settings["exposure_auto"] = cam.ExposureAuto.GetValue()
            if settings["exposure_auto"] != "Continuous":
                settings["exposure_time"] = cam.ExposureTime.GetValue()
            else:
                settings["exposure_time"] = "Auto"
        except Exception:
            pass

        try:
            settings["gain_auto"] = cam.GainAuto.GetValue()
            if settings["gain_auto"] != "Continuous":
                settings["gain"] = cam.Gain.GetValue()
            else:
                settings["gain"] = "Auto"
        except Exception:
            pass

        try:
            settings["frame_rate_enabled"] = cam.AcquisitionFrameRateEnable.GetValue()
            if settings["frame_rate_enabled"]:
                settings["frame_rate"] = cam.AcquisitionFrameRate.GetValue()
        except Exception:
            pass

        try:
            settings["pixel_format"] = str(cam.PixelFormat.GetValue())
        except Exception:
            pass

    except Exception:
        pass

    return settings


def print_camera_settings(camera: BaslerCamera) -> None:
    """Print current camera settings to console."""
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
                print("Exposure Time: Auto")
            else:
                et = float(settings["exposure_time"])
                print(f"Exposure Time: {et:.1f} μs ({et/1000:.2f} ms)")

    if "gain_auto" in settings:
        print(f"Gain Auto: {settings['gain_auto']}")
        if "gain" in settings:
            if settings["gain"] == "Auto":
                print("Gain: Auto")
            else:
                print(f"Gain: {float(settings['gain']):.2f}")

    if "frame_rate" in settings:
        print(f"Frame Rate: {float(settings['frame_rate']):.1f} fps")

    if "pixel_format" in settings:
        print(f"Pixel Format: {settings['pixel_format']}")

    print("=" * 50 + "\n")
