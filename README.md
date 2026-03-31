# Dental Imaging System

A professional dental imaging application for capturing and managing high-quality dental images in clinical environments.

## Features

- **High-Quality Image Capture**: Full-resolution capture (4024×3036) with smooth preview (1920×1080)
- **Hardware Integration**: Basler USB camera and ESP32 LED controller support
- **Touchscreen Interface**: Full-screen kiosk mode optimized for touch interaction
- **Advanced Image Processing**: Digital zoom, ROI selection, color adjustments
- **Flexible Storage**: Local, network, and external storage with DICOM export
- **Reliable Operation**: Automatic error recovery and hardware reconnection

## Requirements

- Python 3.10 or newer
- Windows 10/11
- Basler USB Camera
- ESP32 LED Control Board
- Touchscreen Monitor
- **Basler Pylon SDK** (required for pypylon)

## Installation

### Prerequisites

**Important:** Before installing Python dependencies, you must install the Basler Pylon SDK:

1. Download and install **Basler Pylon SDK** from [Basler's official website](https://www.baslerweb.com/en/products/software/basler-pylon-camera-software-suite/)
2. Install the Pylon SDK (includes drivers and runtime libraries)
3. Restart your computer after installation

### Python Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd dental_image_system
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** `pypylon>=26.2.1` requires the Basler Pylon SDK to be installed on your system. The Python package alone is not sufficient.

## Development

For development, install additional dependencies:
```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
dental_image_system/
├── app/                 # Kiosk UI (PyQt6 + QML) and ``camera_core/`` (Basler + snapshot)
├── config/              # Configuration files
├── firmware/            # ESP32 LED controller (Arduino)
├── kiosk_main.py        # Console entry that runs ``app/main.py``
├── resources/           # Optional assets
├── tests/               # Test suite
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## Configuration

Configuration files are located in the `config/` directory:
- `default_config.json` - Application settings
- `camera_defaults.json` - Camera parameters
- `led_presets.json` - LED preset definitions
- `storage_config.json` - Storage settings

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
