# Project Requirements Implementation Status

Traceability: `project_requirements.txt` (SOW) vs current codebase (`app/` PyQt6+QML + `app/camera_core/` + `firmware/`).

## Implemented (matches SOW intent)

| Area | Requirement | Where / notes |
|------|-------------|----------------|
| Camera | Basler via pypylon, USB, connect/disconnect | `app/camera_core/hardware/camera/basler_camera.py`; `app/camera_service.py` power / auto-connect |
| Camera | Live preview, streaming | `FrameProvider` + QML `image://camera/frame`; `grab_preview_frame`, zoom/crop pipeline |
| Camera | Manual image settings (exposure, gain, WB, contrast, saturation, warmth, tint, …) | `ImageSettingsPanel.qml`, bridge sliders; Basler push for exposure/gain; software color adjust on preview |
| Zoom / ROI | Digital zoom slider, pinch zoom, pan | `main.qml` `PinchArea`, `bridge.zoom` / pan props |
| Zoom / ROI | ROI mode, diagonal box, apply + recenter semantics | `RoiSelectionOverlay.qml`, `bridge.applyRoiSelection` |
| LED | Serial 115200, `DIM:X`, `ON`, `OFF`, `STATUS` | `app/serial_service.py`; `firmware/esp32_led_controller/esp32_led_controller.ino` (+ `ADC`, `RECAL`, `HELP`) |
| LED | Auto-reconnect PCB | `serial_service._ensure_connected`, preferred port, backoff |
| LED | GUI brightness slider; OFF / HIGH / AUTO presets | `BottomBar.qml`, `SettingsPanel.qml`, `bridge` + serial sync |
| LED | Idle auto-off (no video activity) | `SerialService._on_idle_check` + `frameCounterChanged`; `DENTAL_LED_IDLE_MINUTES` |
| Capture | Snapshot + save PNG/JPEG, quality, sound (optional off) | `camera_service.py`, `bridge.captureFormatPng`, `cameraSoundEnabled` |
| Capture | Patient ID naming, use last ID | `bridge.patientId`, `capture_profile.json` |
| Capture | Burst count + interval | `SettingsPanel`, `CameraService` burst timer |
| Capture | Capture delay before shutter | `captureDelaySec` |
| Presets | Three accessible buttons; recall on tap; long-press save + sound | `PresetChip.qml`, `presets.json`, `camera_service` |
| Presets | Presets include LED brightness, zoom, pan, transforms, image sliders | `_preset_snapshot_from_bridge` |
| Storage | Local folder + export dialog; SD target with detection fallback | `storageSdcard`, `_detect_sd_capture_dir`, space thresholds `storage_config.json` |
| Kiosk | Full-screen, frameless | `main.qml` + `main.py` `showFullScreen()` |
| Kiosk | Password-protected exit | `DENTAL_ADMIN_PASSWORD`, `onRequestAppExit` |
| Settings lock | Password to open settings | `DENTAL_SETTINGS_PASSWORD`, `onRequestSettingsUnlock` |
| DICOM | Export captured images as Secondary Capture (pydicom) | `bridge._export_dicom_to_folder`, Settings UI |
| Overlays | Grid, crosshair toggles | `PreviewOverlays.qml` |
| Gestures | 10-point-capable UI (pinch, ROI drag) | QML touch targets; no custom driver |

## Partially implemented / verify on hardware

| Area | Gap | Action |
|------|-----|--------|
| Camera defaults | SOW: full res 4024×3036, **Bayer RG8**, **exposure 10 ms**, **gain 1.0**. `config/camera_defaults.json` currently uses **auto** exposure/gain with 50000 µs / 5.0 when values apply; **no explicit PixelFormat RG8** in `BaslerCamera.configure()` | Align `camera_defaults.json` (or `CameraConfig` + `configure`) with clinical default; set `PixelType` if needed |
| LED sync before capture | SOW: ramp to preset before capture. `config/default_config.json` has `led_stabilization_delay_ms` but **`app/camera_service.py` does not read it**; LEDs track live brightness only | Wire optional pre-capture delay after serial DIM sync (or document intentional omission) |
| Boot splash | SOW: logo splash; `default_config.json` mentions splash; **`app/main.py` does not show a splash window** | Add Qt splash or QML splash using `resources/` if still required |
| SD / export | “Warning at full” — low-space toasts + blocking present; tune thresholds per real file sizes | Production validation |
| Performance | Sub-100 ms preview/capture latency — not formally benchmarked in repo | Measure on target PC + camera |

## Not implemented (SOW or non-functional)

| Item | Notes |
|------|--------|
| **Windows installer** (PyInstaller deliverable) | `scripts/README.md` lists `build_installer.py` as *planned* only — no build script in repo yet |
| **User manual PDF** | `docs/user_manual/` has README only |
| **Formal test report** | Not in repo |
| **Network share / cloud export** (OneDrive, etc.) | Export is folder picker; user may choose a mapped drive manually — no integrated upload |
| **HIPAA: encrypt saved / DICOM images** | DICOM (and PNG/JPG) written **unencrypted** |
| **Swipe to change preset** | Design doc mentions swipe; **only tap / long-press** on preset chips |
| **Multi-language** | English only (SOW: “potentially” multilingual) |
| **Hide Windows taskbar beyond app** | App is fullscreen; **Assigned Access / shell replacement** is deployment concern, not coded |

## Firmware (LED board)

Closed-loop dimming, `DIM` / `ON` / `OFF` / `STATUS` / `ADC` / `RECAL`, idle policy driven by host `OFF`, 5 kHz PWM — aligned with parallel hardware notes from the project (see `esp32_led_controller.ino` header).

## How to keep this file current

After feature or default changes, update the tables above so traceability to `project_requirements.txt` stays accurate.
