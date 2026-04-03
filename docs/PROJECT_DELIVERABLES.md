# What Is Delivered Now — Mapped to Project Requirements

This document lists **what the current codebase ships**, line by line against **`project_requirements.txt`** (SOW). Use it for client handoff and internal sign-off.

**Repository layout (software):** `app/` (PyQt6 + QML UI, `camera_core/` Basler stack), `config/`, `firmware/esp32_led_controller/`, `RunDentalImaging.bat`, `kiosk_main.py`, `requirements.txt`, `docs/`.

---

## Scope (high level)

| SOW scope item | Delivered |
|----------------|-----------|
| Basler control via **pypylon** | Yes — `app/camera_core/`, `app/camera_service.py`. |
| Serial to ESP32 for LED dimming (0–100%) | Yes — `app/serial_service.py` + `firmware/esp32_led_controller/esp32_led_controller.ino`. |
| Full-screen **kiosk** | Yes — `app/main.py`, `app/qml/main.qml` (frameless fullscreen). |
| Touch-friendly GUI, presets for workflows | Yes — QML layout, bottom presets, settings. |
| **Exclude** AI diagnostics, advanced editing | Respected — no AI/editing suite in repo. |
| Logo **boot splash** | Not delivered in `app/main.py` (optional future addition). |

---

## Deliverables (SOW § Deliverables)

| SOW deliverable | Status now | What the client receives |
|-----------------|------------|---------------------------|
| **Source code** Python 3.10+, basler-pypylon, pyserial, opencv-python, PyQt GUI | **Delivered** | Full tree; `requirements.txt` lists PyQt6, pypylon, opencv-python, pyserial, pydicom, etc. |
| **Executable / Windows bundle** (e.g. PyInstaller) | **Supported in-repo** | **`DentalImaging.spec`** + **`build_exe.bat`** produce **`dist/DentalImaging/`** (exe + `_internal`). Ship that folder with **`config/`** beside the exe — see **`docs/BUILD_EXE.md`**. |
| **User manual** (setup, workflows, troubleshooting) | **Delivered** | **`docs/CLIENT_USER_GUIDE.md`** (export to PDF for the contract if required). |
| **Test report** on hardware | **Not a repo artefact** | Functional behaviour is described here and in the user guide; **site acceptance / clinical validation** is performed by the customer or QA partner and documented separately. |

---

## 1. Camera initialization and control

| SOW requirement | Delivered |
|-------------------|-----------|
| Auto-detect / connect Basler via USB; **disconnect** control | Yes — detection + power/connect in UI; `CONNECTED` / `DISCONNECTED` style status in top bar. |
| Defaults: **4024×3036**, **Bayer RG8**, **10 ms** exposure, **gain 1.0** | **Configurable** via `config/camera_defaults.json`; pixel format / exact numbers are deployment-specific — adjust JSON and Basler `configure()` if RG8 must be forced explicitly. |
| Real-time **full-screen** preview, **15–30 fps** class streaming | Yes — grab loop + scaled preview; target FPS in config (e.g. 31). |
| **Image settings** sliders: exposure (~0.001–0.1 s mapped), gain (0–24 dB mapped), WB, contrast, saturation, warmth, tint | Yes — bridge + image settings panel; exposure/gain to camera when connected, rest in software pipeline. |

---

## 2. Zoom and ROI workflow

| SOW requirement | Delivered |
|-------------------|-----------|
| Manual parfocal lens (no motor) | Yes — operator adjusts lens; software has no motorized lens driver. |
| Digital zoom **1×–10×**, **bicubic/Lanczos** style scaling in OpenCV pipeline | Yes — zoom slider + `view_transforms` / crop pipeline using OpenCV resize. |
| **Pinch** zoom, **one-finger pan** | Yes — `PinchArea` in `main.qml`. |
| **Recenter** at current zoom | Yes — **Recenter ROI** / related bridge actions per UI. |
| **ROI mode**, grey overlay, diagonal box, lift finger → center/zoom to region | Yes — `RoiSelectionOverlay.qml` + `applyRoiSelection`. |
| **Swipe** to change preset | **Not implemented** — presets use **tap** and **long-press save** only. |

---

## 3. LED control and sync

| SOW requirement | Delivered |
|-------------------|-----------|
| ESP32 **115200** serial | Yes. |
| Commands **`DIM:X`**, **`ON`**, **`OFF`**, **`STATUS`** | Yes; firmware also supports **`ADC`**, **`RECAL`**, **`HELP`**. |
| Ramp / sync to preset before capture | LEDs track **live** brightness from the app; optional **capture delay** in Settings gives time to settle; dedicated **post-DIM-only** stabilization ms from JSON is not wired separately. |
| **Auto-off** after idle (no video activity) | Yes — `SerialService` idle timer + `DENTAL_LED_IDLE_MINUTES`. |
| GUI: **slider** 0–100%, **OFF / HIGH** (and AUTO), manual override | Yes — bottom bar + settings LED preset controls. |
| Subtle **touch / UI sounds** | Yes — capture and preset feedback where implemented; camera sound toggle in Settings. |

---

## 4. Capture and saving

| SOW requirement | Delivered |
|-------------------|-----------|
| **CAPTURE** grabs frame | Yes — right rail + optional Space key. |
| **PC local** PNG/JPEG, date/time/**Patient ID** naming | Yes — `SnapshotWriter` + patient ID field; paths under configured capture root. |
| **SD card** path / auto-detect / low-space **warnings** | Yes — storage target in Settings + `storage_config.json` thresholds. |
| **Network share / cloud** (“easy”) | **No dedicated OneDrive button** — customer may choose a **network or synced folder** in the **Export** / folder dialogs. |
| **DICOM** export (pydicom) | Yes — Settings **DICOM** export (Secondary Capture style). |
| **Burst** sequence (count + interval) | Yes — Settings burst mode + interval. |
| **Camera sound**; **option to turn off** | Yes — Settings toggle. |

---

## 5. Presets (dental workflow)

| SOW requirement | Delivered |
|-------------------|-----------|
| **Three** accessible preset buttons | Yes — bottom bar `PresetChip`s. |
| **Tap** applies; **long-press** saves with **sound** | Yes. |
| Apply **camera + LED** related settings from snapshot | Yes — preset JSON includes brightness, zoom, pan, transforms, image sliders; recall pushes exposure/gain to camera. |

---

## 6. GUI and usability

| SOW requirement | Delivered |
|-------------------|-----------|
| Touch-friendly, PyQt responsive design | Yes — PyQt6 + QML. |
| Layout: large preview, side/bottom **sliders**, **presets**, **capture**, **LED** | Yes. |
| Kiosk fullscreen; **password** to shut down | Yes — fullscreen + admin password (`DENTAL_ADMIN_PASSWORD`). Taskbar hiding is primarily **Windows / Assigned Access** beyond the app window. |
| Tooltips | Yes — on multiple rail buttons. |
| **Multi-language** | **English only** in current QML. |

---

## Non-functional requirements (summary)

| Topic | Delivered / note |
|-------|------------------|
| **Performance** | Streaming and capture tuned for interactive use; sub-100 ms latency is a design goal, not a guaranteed measured spec in this document. |
| **Windows 11**, USB 3.0 camera | Supported target platform; camera throughput depends on hardware. |
| **Password-protect settings** | Yes — `DENTAL_SETTINGS_PASSWORD`. |
| **Encrypt** saved / DICOM images (HIPAA wording in SOW) | **Not in-application** — use disk encryption / clinic policy for PHI at rest. |
| **Reliability** | Camera errors surfaced; **ESP32 auto-reconnect** and backoff in `serial_service.py`. |
| **DICOM / standards alignment** | Export path for interoperability; formal **modality conformance** is site responsibility. |

---

## Hardware / monitor notes (SOW — Elo 1502LM)

Software targets **1920×1080** full-screen preview with **multi-touch** (pinch, ROI). Physical monitor certifications (IEC 60601, IP-22) apply to **hardware purchase**, not to this software package.

---

## Firmware

**Delivered:** `firmware/esp32_led_controller/esp32_led_controller.ino` — PWM on GPIO2, **DRIVE_ADC** feedback on GPIO8, closed-loop dim to CRTL voltage spec, serial protocol as documented in sketch header.

---

## One-page summary for the client

| Category | Delivered product |
|----------|-------------------|
| ** Application** | Full-screen dental kiosk: live Basler preview, zoom/ROI, capture/burst, export + DICOM, touch UI. |
| **Illumination** | ESP32 firmware + PC serial service (`DIM` / `ON` / `OFF` / `STATUS`, idle off, reconnect). |
| **Operator start** | `RunDentalImaging.bat` + `docs/CLIENT_USER_GUIDE.md`. |
| **Config** | `config/*.json` for camera, storage, defaults, presets. |
| **Gaps vs literal SOW** | No PyInstaller **.exe** in repo; no formal **test report** file; no **boot splash**; no **swipe** preset; no **in-app encryption**; network/cloud via **folder choice** only. |

---

*Generated for traceability to `project_requirements.txt`. Update this file when the scope changes.*
