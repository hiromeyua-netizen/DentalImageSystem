"""
Test script for camera preview display.

This script creates a GUI window to display live camera feed.
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dental_imaging.ui.main_window import MainWindow
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.exceptions import CameraNotFoundError


def main():
    """Run camera preview test."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Dental Imaging System - Camera Preview Test")
    
    # Load camera configuration
    config_path = PROJECT_ROOT / "config" / "camera_defaults.json"
    print(f"Loading configuration from: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        config = CameraConfig.from_dict(config_dict)
        print(f"Configuration loaded:")
        print(f"  Resolution: {config.resolution}")
        print(f"  Exposure: {'Auto' if config.exposure.auto else config.exposure.value}μs")
        print(f"  Gain: {'Auto' if config.gain.auto else config.gain.value}")
        print(f"  Frame Rate: {config.frame_rate} fps")
        print()
        
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        print("Please ensure config/camera_defaults.json exists.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create main window
    window = MainWindow()
    
    # Initialize camera
    print("Initializing camera...")
    if not window.initialize_camera(config):
        print("Failed to initialize camera. Exiting.")
        sys.exit(1)
    
    print("Camera initialized successfully!")
    print("\nInstructions:")
    print("1. Click 'Start Preview' to begin live preview")
    print("2. Click 'Stop Preview' to stop preview")
    print("3. Click 'Capture' to capture a full-resolution image")
    print("4. Close the window to exit")
    print()
    
    # Show window
    window.show()
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
