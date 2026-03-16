"""
Main entry point for the Dental Imaging System application.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dental_imaging.ui.main_window import MainWindow


def main():
    """Application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Dental Imaging System")
    app.setApplicationVersion("0.1.0")
    
    # Note: High DPI scaling is enabled by default in PyQt6
    # No need to set AA_EnableHighDpiScaling or AA_UseHighDpiPixmaps
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
