# Project Requirements Implementation Status

This checklist tracks the current implementation state against `project_requirements.txt`.

## Completed

- Camera detect/connect/disconnect workflow with live preview and stream stats
- Manual image settings controls (exposure, gain, white balance, contrast, saturation, warmth, tint)
- Digital zoom, pinch gesture, one-finger pan, ROI select/apply, recenter
- Overlay toggles (grid and crosshair)
- Capture in snapshot and burst modes with optional delay
- Capture save with PNG/JPG selection and quality setting
- Patient ID naming workflow and "use last patient ID" option
- Capture confirmation modal and capture preview modal/gallery
- Export all captured images to selected folder with collision-safe renaming
- Export completion modal with folder path and quick "Open Folder" action
- Storage target selection (SYSTEM / SD CARD) with fallback handling and user status text
- Storage free-space guards: low-space warnings and export/capture blocking on critically low space
- Storage thresholds are configurable via `config/storage_config.json` (`space_thresholds`)
- ESP32 serial service (auto-detect, reconnect, status polling, brightness sync)
- LED preset behavior (AUTO follows slider, manual fixed 50%)
- Kiosk full-screen mode with password-protected exit

## Partially Implemented

- Basler default initialization values from SOW: implemented via camera defaults file when present; verify exact exposure/gain defaults on production hardware
- SD card full-capacity warning: implemented for capture/export paths; validate thresholds on production image sizes
- Preset long-press save with sound confirmation: save/recall exists; long-press UX and confirmation sound should be verified end-to-end
- Dentist workflow validation/testing report: core features implemented, but formal test report still pending

## Pending

- Installer packaging workflow for Windows 11 (PyInstaller deliverable)
- User manual PDF (setup, workflows, troubleshooting)
- Optional advanced exports mentioned in SOW (network share/cloud/DICOM)
- Optional password protection for settings panel access (separate from kiosk exit)
- Optional idle-based LED auto-off timer (minutes without video feed activity)

## Notes

- Keep this file updated after each feature batch to maintain implementation traceability.
