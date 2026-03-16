"""
Test script for camera detection functionality.

This script can be run to verify that camera detection is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dental_imaging.hardware.camera import (
    detect_cameras,
    get_camera_count,
    get_first_available_camera,
    CameraInfo,
)


def main():
    """Test camera detection."""
    print("=" * 60)
    print("Camera Detection Test")
    print("=" * 60)
    print()
    
    try:
        # Get camera count
        count = get_camera_count()
        print(f"Number of cameras detected: {count}")
        print()
        
        if count == 0:
            print("No cameras found. Please ensure:")
            print("1. Basler camera is connected via USB")
            print("2. Basler Pylon SDK is installed")
            print("3. Camera drivers are properly installed")
            return
        
        # Detect all cameras
        print("Detecting all cameras...")
        cameras = detect_cameras()
        
        print(f"\nFound {len(cameras)} camera(s):\n")
        
        for i, camera in enumerate(cameras, 1):
            print(f"Camera {i}:")
            print(f"  Serial Number: {camera.serial_number}")
            print(f"  Model Name: {camera.model_name}")
            print(f"  Vendor Name: {camera.vendor_name}")
            print(f"  Friendly Name: {camera.friendly_name}")
            print(f"  User Defined Name: {camera.user_defined_name}")
            print(f"  Device Class: {camera.device_class}")
            print()
        
        # Get first available camera
        first_camera = get_first_available_camera()
        if first_camera:
            print("First available camera:")
            print(f"  Serial: {first_camera.serial_number}")
            print(f"  Model: {first_camera.model_name}")
        
        print("\n" + "=" * 60)
        print("Camera detection test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during camera detection: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Basler Pylon SDK is installed")
        print("2. Check that camera is connected and powered")
        print("3. Verify camera drivers are installed")
        sys.exit(1)


if __name__ == "__main__":
    main()
