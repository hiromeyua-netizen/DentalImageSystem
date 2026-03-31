"""
Test script for camera connection and basic operations.

This script tests camera initialization, configuration, and frame grabbing.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from camera_core.exceptions import CameraConnectionError, CameraNotFoundError
from camera_core.hardware.camera import BaslerCamera, get_first_available_camera
from camera_core.models.camera_config import CameraConfig


def main():
    """Test camera connection and operations."""
    print("=" * 60)
    print("Camera Connection Test")
    print("=" * 60)
    print()
    
    try:
        # Get first available camera
        print("Detecting camera...")
        camera_info = get_first_available_camera()
        
        if not camera_info:
            print("ERROR: No camera found!")
            return
        
        print(f"Found camera: {camera_info.model_name} (Serial: {camera_info.serial_number})")
        print()
        
        # Load camera configuration
        config_path = PROJECT_ROOT / "config" / "camera_defaults.json"
        print(f"Loading configuration from: {config_path}")
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        config = CameraConfig.from_dict(config_dict)
        print(f"Configuration loaded:")
        print(f"  Resolution: {config.resolution}")
        print(f"  Exposure: {'Auto' if config.exposure.auto else config.exposure.value}μs")
        print(f"  Gain: {'Auto' if config.gain.auto else config.gain.value}")
        print(f"  Frame Rate: {config.frame_rate} fps")
        print()
        
        # Connect to camera
        print("Connecting to camera...")
        camera = BaslerCamera(camera_info)
        camera.connect()
        print("✓ Camera connected successfully")
        print()
        
        # Configure camera
        print("Configuring camera...")
        camera.configure(config)
        print("✓ Camera configured successfully")
        print()
        
        # Test single frame grab
        print("Testing single frame grab...")
        frame = camera.grab_frame(timeout_ms=5000)
        
        if frame is not None:
            print(f"✓ Frame grabbed successfully")
            print(f"  Frame shape: {frame.shape}")
            print(f"  Frame dtype: {frame.dtype}")
        else:
            print("✗ Frame grab failed")
        
        print()
        
        # Test preview frame grab
        print("Testing preview frame grab (1920x1080)...")
        preview_frame = camera.grab_preview_frame(1920, 1080)
        
        if preview_frame is not None:
            print(f"✓ Preview frame grabbed successfully")
            print(f"  Preview shape: {preview_frame.shape}")
        else:
            print("✗ Preview frame grab failed")
        
        print()
        
        # Test continuous grabbing
        print("Testing continuous grabbing (3 frames)...")
        camera.start_grabbing()
        print("✓ Continuous grabbing started")
        
        for i in range(3):
            frame = camera.grab_frame()
            if frame is not None:
                print(f"  Frame {i+1}: ✓ (shape: {frame.shape})")
            else:
                print(f"  Frame {i+1}: ✗ Failed")
        
        camera.stop_grabbing()
        print("✓ Continuous grabbing stopped")
        print()
        
        # Disconnect
        print("Disconnecting from camera...")
        camera.disconnect()
        print("✓ Camera disconnected")
        print()
        
        print("=" * 60)
        print("All tests passed successfully!")
        print("=" * 60)
        
    except CameraNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Basler camera is connected via USB")
        print("2. Check that Basler Pylon SDK is installed")
        print("3. Verify camera drivers are installed")
        sys.exit(1)
        
    except CameraConnectionError as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check camera connection")
        print("2. Ensure no other application is using the camera")
        print("3. Try unplugging and reconnecting the camera")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
