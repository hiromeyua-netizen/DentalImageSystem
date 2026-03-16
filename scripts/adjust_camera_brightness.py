"""
Interactive script to adjust camera brightness by testing different exposure/gain values.
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dental_imaging.hardware.camera import BaslerCamera, get_first_available_camera
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.hardware.camera.camera_settings_helper import print_camera_settings
from dental_imaging.exceptions import CameraNotFoundError, CameraConnectionError


def main():
    """Interactive brightness adjustment."""
    print("=" * 60)
    print("Camera Brightness Adjustment Tool")
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
        
        # Connect
        print("Connecting to camera...")
        camera = BaslerCamera(camera_info)
        camera.connect()
        camera.configure(config)
        
        # Get exposure and gain ranges
        exp_min, exp_max = camera.get_exposure_range()
        gain_min, gain_max = camera.get_gain_range()
        
        print(f"\nCamera ranges:")
        print(f"  Exposure: {exp_min:.0f} - {exp_max:.0f} μs ({exp_min/1000:.1f} - {exp_max/1000:.1f} ms)")
        print(f"  Gain: {gain_min:.1f} - {gain_max:.1f}")
        print()
        
        # Current settings
        print("Current settings:")
        print_camera_settings(camera)
        
        print("\n" + "=" * 60)
        print("Brightness Adjustment Suggestions:")
        print("=" * 60)
        print()
        print("If image is still too dark, try:")
        print()
        print("1. Increase exposure time:")
        print(f"   - Current: {config.exposure.value}μs ({config.exposure.value/1000:.1f}ms)")
        print(f"   - Try: 200000μs (200ms) or higher")
        print(f"   - Max available: {exp_max:.0f}μs ({exp_max/1000:.1f}ms)")
        print()
        print("2. Increase gain:")
        print(f"   - Current: {config.gain.value}")
        print(f"   - Try: 15.0 or higher")
        print(f"   - Max available: {gain_max:.1f}")
        print()
        print("3. Enable auto-exposure and auto-gain:")
        print("   - Set 'exposure.auto' to true in config")
        print("   - Set 'gain.auto' to true in config")
        print()
        print("=" * 60)
        print()
        
        # Test different values
        print("Testing recommended values...")
        print()
        
        test_values = [
            (200000, 15.0, "High exposure + High gain"),
            (300000, 20.0, "Very high exposure + Very high gain"),
            (500000, 25.0, "Maximum brightness"),
        ]
        
        for exp, gain, desc in test_values:
            if exp > exp_max:
                exp = exp_max
            if gain > gain_max:
                gain = gain_max
            
            print(f"Testing: {desc}")
            print(f"  Exposure: {exp}μs ({exp/1000:.1f}ms), Gain: {gain:.1f}")
            
            try:
                camera.set_exposure(exp, auto=False)
                camera.set_gain(gain, auto=False)
                
                # Grab a test frame
                frame = camera.grab_frame()
                if frame is not None:
                    # Calculate average brightness
                    brightness = frame.mean()
                    print(f"  ✓ Frame captured - Average brightness: {brightness:.1f}")
                    print(f"    (Higher is brighter, typical range: 50-200)")
                else:
                    print(f"  ✗ Failed to grab frame")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            
            print()
        
        # Restore original config
        print("Restoring original configuration...")
        camera.configure(config)
        print_camera_settings(camera)
        
        print("\nTo apply these settings permanently, edit config/camera_defaults.json")
        print("with the values that worked best for you.")
        print()
        
        # Disconnect
        camera.disconnect()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
