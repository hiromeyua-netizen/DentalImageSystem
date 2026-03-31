"""
Diagnostic script to check camera settings and suggest fixes for dark images.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from camera_core.exceptions import CameraConnectionError, CameraNotFoundError
from camera_core.hardware.camera import BaslerCamera, get_first_available_camera
from camera_core.hardware.camera.camera_settings_helper import (
    get_camera_settings,
    print_camera_settings,
)
from camera_core.models.camera_config import CameraConfig


def main():
    """Diagnose camera settings."""
    print("=" * 60)
    print("Camera Settings Diagnostic")
    print("=" * 60)
    print()
    
    try:
        # Get camera
        camera_info = get_first_available_camera()
        if not camera_info:
            print("ERROR: No camera found!")
            return
        
        print(f"Camera: {camera_info.model_name} (Serial: {camera_info.serial_number})")
        print()
        
        # Load config
        config_path = PROJECT_ROOT / "config" / "camera_defaults.json"
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        config = CameraConfig.from_dict(config_dict)
        
        print("Configuration from file:")
        print(f"  Exposure: {'Auto' if config.exposure.auto else f'{config.exposure.value}μs'}")
        print(f"  Gain: {'Auto' if config.gain.auto else f'{config.gain.value}'}")
        print()
        
        # Connect and configure
        print("Connecting to camera...")
        camera = BaslerCamera(camera_info)
        camera.connect()
        camera.configure(config)
        
        print("Camera connected and configured.")
        print()
        
        # Get actual settings
        print("Actual camera settings:")
        settings = get_camera_settings(camera)
        print_camera_settings(camera)
        
        # Diagnose issues
        print("Diagnosis:")
        print("-" * 60)
        
        issues = []
        suggestions = []
        
        # Check exposure
        if "exposure_auto" in settings:
            if settings["exposure_auto"] != "Continuous":
                exp_time = settings.get("exposure_time", 0)
                if exp_time < 20000:  # Less than 20ms
                    issues.append(f"Exposure time is very short: {exp_time:.1f}μs")
                    suggestions.append("Enable auto-exposure or increase exposure time to at least 20000μs (20ms)")
            else:
                print("✓ Auto-exposure is enabled")
        else:
            issues.append("Could not read exposure settings")
        
        # Check gain
        if "gain_auto" in settings:
            if settings["gain_auto"] != "Continuous":
                gain = settings.get("gain", 0)
                if gain < 3.0:
                    issues.append(f"Gain is very low: {gain:.2f}")
                    suggestions.append("Enable auto-gain or increase gain to at least 3.0")
            else:
                print("✓ Auto-gain is enabled")
        else:
            issues.append("Could not read gain settings")
        
        # Print issues
        if issues:
            print("⚠ Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            print()
            print("💡 Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        else:
            print("✓ No obvious issues found with exposure/gain settings")
        
        print()
        print("If image is still dark:")
        print("  1. Check lighting conditions")
        print("  2. Verify camera lens is not covered")
        print("  3. Try increasing exposure time manually")
        print("  4. Try increasing gain manually")
        print()
        
        # Disconnect
        camera.disconnect()
        
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
