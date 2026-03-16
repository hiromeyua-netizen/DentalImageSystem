# Dental Imaging System Software

## Application Workflow, Development Stack, and Development Phases

------------------------------------------------------------------------

# 1. Application Workflow

The application workflow describes how the dental imaging system behaves
from startup to image capture and storage. The workflow is designed to
prioritize **speed, reliability, and ease of use** for dentists
operating in a clinical environment.

The goal is to allow the dentist to capture high‑quality dental images
with **minimal interaction and minimal distraction** during procedures.

The entire workflow can be divided into the following stages:

-   System Startup
-   Hardware Initialization
-   Live Preview Operation
-   Image Framing and Adjustment
-   Image Capture
-   Image Storage and Export
-   Error Handling and Recovery

------------------------------------------------------------------------

## 1.1 System Startup Workflow

When the system powers on, the software launches automatically in
**kiosk mode** so that the user interacts only with the dental imaging
interface.

### Startup Process

1.  Windows boots on the Mini PC.
2.  The imaging software launches automatically.
3.  A splash screen appears showing the system logo.
4.  The application begins hardware initialization.
5.  The user interface loads in full-screen kiosk mode.
6.  The live camera preview begins automatically.

### Startup Goals

-   No manual launching of software
-   No visible Windows interface
-   System ready for capture within a few seconds

------------------------------------------------------------------------

## 1.2 Hardware Initialization Workflow

During startup the software attempts to detect and connect to the
required hardware components.

### Hardware Components

-   Basler USB Camera
-   ESP32 LED Control Board
-   Touchscreen Monitor

### Initialization Steps

1.  Search for Basler camera via pypylon.
2.  Attempt to connect to the camera.
3.  Load default camera parameters:
    -   Full resolution
    -   Default exposure
    -   Default gain
4.  Scan available serial ports.
5.  Attempt connection to the ESP32 LED controller.
6.  Set LED brightness to default level.
7.  Start preview stream.

### Failure Handling

If hardware is missing:

-   The system displays a clear message
-   The software retries connection automatically
-   The UI remains responsive

Example message:

Camera not detected. Attempting reconnect.

------------------------------------------------------------------------

## 1.3 Live Preview Operation

The live preview allows the dentist to position the camera and frame the
tooth before capturing an image.

### Preview Characteristics

Preview uses a **reduced resolution stream** to maintain smooth
performance.

Preview Resolution: 1920 × 1080

Capture Resolution: 4024 × 3036

### Preview Processing Pipeline

Camera Frame\
↓\
ROI Processing\
↓\
Digital Zoom Processing\
↓\
Color Adjustment\
↓\
Display to Screen

This pipeline ensures smooth preview performance while maintaining high
quality capture capability.

------------------------------------------------------------------------

## 1.4 Image Framing and Adjustment

Before capturing an image, the dentist may adjust the view using several
tools.

### Available Adjustments

Zoom\
ROI Selection\
Pan\
Brightness Control\
Preset Selection

### Zoom

Digital zoom is implemented using image cropping followed by
interpolation.

Zoom Range:

1× to 10×

Zoom allows the dentist to view either:

-   Full mouth area
-   Single tooth close-up

------------------------------------------------------------------------

### ROI Selection

ROI (Region of Interest) allows the dentist to draw a box around a
specific part of the image.

ROI Workflow:

1.  Press ROI Mode.
2.  Drag finger diagonally across the screen.
3.  The selected area becomes the active view.
4.  The system automatically centers and zooms into that area.

------------------------------------------------------------------------

### Presets

Presets allow the dentist to instantly switch between common imaging
configurations.

Examples:

Wide View\
Medium View\
Tight Tooth View

Presets may store:

-   Zoom level
-   LED brightness
-   Exposure settings

Custom presets can be saved using a long press gesture.

------------------------------------------------------------------------

## 1.5 Image Capture Workflow

Capturing an image must be extremely fast and reliable.

### Capture Steps

1.  Dentist presses CAPTURE button.
2.  LED brightness is adjusted if necessary.
3.  The system waits briefly for lighting stabilization.
4.  A full-resolution frame is captured.
5.  A shutter sound is played.
6.  The captured image is sent to the storage manager.

### Timing Requirements

LED stabilization delay: 50 milliseconds

Total capture time target: Less than 150 milliseconds

------------------------------------------------------------------------

## 1.6 Image Storage Workflow

Captured images must be saved safely and organized properly.

### File Naming Strategy

Images are automatically named using:

Date\
Time\
Patient ID

Example filename:

2026-03-10_14-05-32_patient123.png

### Folder Structure

DentalImages/

Patient_123/

2026-03-10_14-05-32.png

2026-03-10_14-07-10.png

------------------------------------------------------------------------

### Storage Locations

Images can be saved to:

Local PC storage\
Network server\
External storage device\
DICOM export format

The storage manager handles file organization and format conversion.

------------------------------------------------------------------------

## 1.7 Error Handling and Recovery

The software must remain stable even if hardware disconnects.

### Example Error Scenarios

Camera disconnected\
LED controller unplugged\
Storage drive full\
Network unavailable

### Recovery Strategy

The application automatically:

-   Detects errors
-   Displays clear messages
-   Attempts reconnection
-   Prevents application crashes

------------------------------------------------------------------------

# 2. Development Stack

The development stack defines the software technologies used to build
the dental imaging system.

The stack is designed to prioritize:

-   Hardware compatibility
-   Performance
-   Maintainability
-   Ease of deployment

------------------------------------------------------------------------

## 2.1 Programming Language

Python 3.10 or newer

Python is selected because:

-   Strong hardware integration support
-   Large ecosystem of libraries
-   Fast development cycle
-   Good compatibility with Basler SDK

------------------------------------------------------------------------

## 2.2 GUI Framework

PyQt6

PyQt provides:

-   Modern UI capabilities
-   Touchscreen support
-   Hardware acceleration
-   Flexible layout design

PyQt is preferred over Tkinter due to better performance and visual
quality.

------------------------------------------------------------------------

## 2.3 Camera SDK

Basler pypylon SDK

This SDK provides direct control of Basler cameras including:

Camera discovery\
Image streaming\
Exposure control\
Gain adjustment\
White balance control

------------------------------------------------------------------------

## 2.4 Image Processing

OpenCV

OpenCV is used for:

Image resizing\
Digital zoom\
ROI cropping\
Color adjustment\
Frame conversion

OpenCV provides fast C++ optimized image processing functions.

------------------------------------------------------------------------

## 2.5 Serial Communication

PySerial

PySerial enables communication with the ESP32 LED controller.

Functions include:

Opening serial ports\
Sending commands\
Receiving device status

------------------------------------------------------------------------

## 2.6 DICOM Support

pydicom

The pydicom library allows the software to export images in DICOM format
for integration with dental imaging systems.

------------------------------------------------------------------------

## 2.7 Packaging and Deployment

PyInstaller

PyInstaller converts the Python application into a standalone executable
installer for Windows systems.

Benefits include:

No Python installation required\
Easy installation for clinics\
Simplified deployment

------------------------------------------------------------------------

## 2.8 Configuration Management

JSON configuration files are used for:

Default camera settings\
LED presets\
Storage locations\
System preferences

------------------------------------------------------------------------

# 3. Development Phase Breakdown

Development should be divided into structured phases to reduce risk and
ensure steady progress.

Each phase builds on the previous phase.

------------------------------------------------------------------------

## Phase 1 --- Core Camera Integration

Goal:

Establish stable communication with the Basler camera and display a live
preview.

Tasks:

Install pypylon SDK\
Detect connected cameras\
Implement camera initialization\
Start live preview stream\
Display preview in GUI window\
Capture single frame functionality

Deliverables:

Working camera preview\
Basic capture capability

Estimated Time:

3--4 weeks

------------------------------------------------------------------------

## Phase 2 --- GUI Development

Goal:

Create the full touchscreen user interface.

Tasks:

Design main application window\
Implement preview display area\
Add capture button\
Add LED brightness controls\
Add preset buttons\
Add ROI selection tools

Deliverables:

Complete user interface\
Touchscreen interaction support

Estimated Time:

3 weeks

------------------------------------------------------------------------

## Phase 3 --- Hardware Integration

Goal:

Integrate the LED controller and synchronize lighting with image
capture.

Tasks:

Implement serial communication with ESP32\
Add LED brightness slider\
Implement LED presets\
Add LED synchronization during capture

Deliverables:

Fully integrated lighting control

Estimated Time:

2 weeks

------------------------------------------------------------------------

## Phase 4 --- Image Processing Features

Goal:

Implement advanced imaging tools.

Tasks:

Digital zoom system\
ROI cropping tools\
Color balance adjustments\
Image rotation and flipping

Deliverables:

Enhanced imaging capabilities

Estimated Time:

2--3 weeks

------------------------------------------------------------------------

## Phase 5 --- Storage and Export

Goal:

Add robust storage and export capabilities.

Tasks:

Implement storage manager\
Create folder organization system\
Implement DICOM export\
Add network storage support

Deliverables:

Reliable image storage and export system

Estimated Time:

2--3 weeks

------------------------------------------------------------------------

## Phase 6 --- Stability and Optimization

Goal:

Prepare the system for real clinical use.

Tasks:

Error handling improvements\
Hardware reconnection logic\
Performance optimization\
User testing with dentists

Deliverables:

Production‑ready software

Estimated Time:

2 weeks

------------------------------------------------------------------------

# Summary

The dental imaging system software is designed to provide a streamlined
workflow that allows dentists to capture high-quality images quickly and
reliably.

By combining a well‑structured application workflow, a robust
development stack, and a phased development plan, the system can be
developed efficiently while maintaining high reliability and usability
in clinical environments.
