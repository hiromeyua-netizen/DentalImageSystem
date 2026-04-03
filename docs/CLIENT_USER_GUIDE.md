# Dental Imaging System — Client User Guide

**Document version:** 1.0  
**Application:** Dental Imaging System (PyQt6 kiosk UI + Basler camera + ESP32 LED controller)  
**Audience:** Clinic IT staff and clinical operators  

This guide describes installation, daily operation, and troubleshooting. For a **line-by-line list of what the project delivers versus `project_requirements.txt`**, see **`PROJECT_DELIVERABLES.md`** in the same folder. A short checklist is also in [Appendix A](#appendix-a-requirements-implementation-checklist).

---

## Table of contents

1. [Overview](#1-overview)  
2. [What you need before installation](#2-what-you-need-before-installation)  
3. [Installing and running the software](#3-installing-and-running-the-software)  
4. [Main screen layout](#4-main-screen-layout)  
5. [Camera](#5-camera)  
6. [Image settings](#6-image-settings)  
7. [Zoom, pan, ROI](#7-zoom-pan-roi)  
8. [LED illumination (ESP32)](#8-led-illumination-esp32)  
9. [Capture, burst, and sound](#9-capture-burst-and-sound)  
10. [Patient ID and storage](#10-patient-id-and-storage)  
11. [Presets](#11-presets)  
12. [Settings panel](#12-settings-panel)  
13. [Kiosk mode, exit, and passwords](#13-kiosk-mode-exit-and-passwords) (how to **change passwords**)  
14. [Configuration files](#14-configuration-files)  
15. [Troubleshooting](#15-troubleshooting)  
16. [Appendix A — Requirements implementation checklist](#appendix-a-requirements-implementation-checklist)  
17. [Appendix B — Optional Windows kiosk hardening](#appendix-b-optional-windows-kiosk-hardening)  

---

## 1. Overview

The application provides:

- **Live preview** from a **Basler USB3** area-scan camera (e.g. 12 MP class sensors), scaled for full-screen viewing on a **1920×1080** touch display.  
- **Digital zoom** (slider and pinch), **pan**, and **ROI** workflow for tight views.  
- **Software image adjustments** (exposure, gain, white balance, contrast, saturation, warmth, tint) with touch-friendly controls.  
- **Synchronized LED illumination** via **serial** link to an **ESP32** controller (`DIM` / `ON` / `OFF` / `STATUS`).  
- **Snapshot and burst capture** with optional delay; **PNG or JPEG** saving; **patient ID** in filenames.  
- **Export** of captured images to a chosen folder; optional **DICOM (Secondary Capture)** export for interoperability.  
- **Full-screen kiosk** operation with **password-protected** application exit and **password-protected** settings panel.  

**Not included in software:** AI diagnostics, advanced image editing, built-in cloud upload, or encryption of files at rest. Use clinic policies (e.g. BitLocker, network share permissions) for protecting patient data where required.

---

## 2. What you need before installation

| Item | Notes |
|------|--------|
| **PC** | Windows **10 or 11** (64-bit). Project targets mini PCs with USB 3.0. |
| **Python** | **3.10 or newer**, available on PATH (or use the **Windows “py” launcher**). |
| **Basler Pylon** | **Pylon Camera Software Suite** installed *before* first run so **pypylon** can access the camera. Download from [Basler Pylon](https://www.baslerweb.com/en/products/software/basler-pylon-camera-software-suite/). Reboot after install if the installer recommends it. |
| **Camera** | Basler USB 3.0 camera (e.g. acA4024-29uc class); USB 3.0 cable and port strongly recommended. |
| **ESP32 LED board** | USB serial at **115200 baud**; drivers installed (e.g. CP210x/CH340 as applicable). |
| **Touch display** | Full HD recommended (e.g. 15.6" medical touch); multi-touch for pinch and ROI. |
| **Application folder** | Complete project tree: at minimum `app/`, `config/`, `requirements.txt`, and `RunDentalImaging.bat`. |

---

## 3. Installing and running the software

### 3.1 Quick launch (recommended for operators)

1. Copy the **entire application folder** onto the kiosk PC.  
2. Install **Basler Pylon** (if not already installed).  
3. Double-click **`RunDentalImaging.bat`** in the project root.  

The batch file will:

- Create a **`venv`** folder (first run only) for an isolated Python environment.  
- Install dependencies from **`requirements.txt`**.  
- Start **`app/main.py`**.  

If a step fails, a message is shown; fix the issue (often Python not on PATH or no internet for pip) and run the batch file again.

### 3.1b Packaged executable (no Python on the kiosk)

If you distribute a **PyInstaller** build (see **`docs/BUILD_EXE.md`**):

1. Copy the whole **`DentalImaging`** folder from **`dist\DentalImaging\`** (contains **`DentalImaging.exe`** and **`_internal`**).  
2. Place the repo’s **`config`** folder **next to** **`DentalImaging.exe`** (same folder as **`_internal`**).  
3. Install **Basler Pylon** on that PC.  
4. Run **`DentalImaging.exe`**.  

Captures and presets typically write under that same folder (e.g. **`captures`**, **`config\presets.json`**).

### 3.2 Manual launch (IT / developers)

From the project root, with dependencies installed:

```text
python app\main.py
```

Alternatively, after `pip install -e .`, the console entry **`dental-imaging`** may be used if configured in your environment.

### 3.3 First-time checklist

- [ ] Pylon installed; camera appears in Basler **pylon Viewer**.  
- [ ] USB 3.0 port used for the camera.  
- [ ] ESP32 COM port available in Device Manager when plugged in.  
- [ ] Screen resolution and Windows **touch calibration** completed if needed.  

---

## 4. Main screen layout

| Area | Purpose |
|------|---------|
| **Center** | **Live preview** (full bleed). Overlays optional: **grid**, **crosshair** (Settings). |
| **Top bar** | System title, **CONNECTED / DISCONNECTED** camera status, **power** control for camera session, optional LED controller status text. |
| **Bottom bar** | **Brightness** slider (LED), **zoom** slider, **three preset chips** (recall / long-press save). |
| **Right rail** | **Capture** (snapshot/burst), **ROI mode**, **recenter ROI**, **auto colour**, **rotate** / **flip**, **image settings**, **settings** (gear). |

Tooltips appear on several rail buttons.

---

## 5. Camera

- **Connect:** tap the **power** control in the top bar to start the camera session when a Basler device is detected.  
- **Disconnect:** tap again to stop streaming and release the camera (useful before unplugging USB).  
- **Detection:** if no camera is found, status text hints **USB**, **drivers**, or **Pylon** installation.  
- **Defaults:** resolution and exposure/gain behaviour are driven by **`config/camera_defaults.json`** when present (full-resolution capture path is supported per your deployment file).  

---

## 6. Image settings

Open **Image settings** from the right rail.

Sliders (typical ranges mapped in software):

- **Exposure** and **gain** — pushed to the **Basler** when connected (hardware).  
- **White balance, contrast, saturation, warmth, tint** — applied in **software** on the preview (and capture pipeline as implemented).  

A **reset to defaults** action may be available to restore neutral / auto behaviours depending on deployment.

---

## 7. Zoom, pan, ROI

- **Digital zoom:** bottom bar **zoom** slider (approximately **1×–10×** behaviour via crop/scale).  
- **Pinch to zoom:** two-finger pinch on the preview (when **not** in ROI draw mode).  
- **Pan:** drag with one finger when zoomed.  
- **ROI mode:** enable **ROI** on the right rail; draw a **diagonal box** on the preview; on release, the view **recenters and zooms** to that region.  
- **Recenter ROI:** button on the right rail restores ROI framing behaviour per application logic.  

The physical **C-mount / parfocal lens** is adjusted manually on the hardware (no motorized lens control in software).

---

## 8. LED illumination (ESP32)

- **Serial:** **115200 baud**, newline-terminated commands.  
- **Brightness:** bottom bar **slider** (0–100%) sends **`DIM:X`**.  
- **Presets in settings / bottom area:** **AUTO** (follows slider), **manual OFF / HIGH** chips as provided in the UI.  
- **Idle auto-off:** after a configurable period **without live video activity**, the app may send **`OFF`** to save power (default tied to environment variable **`DENTAL_LED_IDLE_MINUTES`**, typically 5 minutes).  
- **Reconnection:** if the USB serial device drops, the service **retries** connection in the background when possible.  

**Operator note:** ensure only **one** program uses the ESP32 COM port at a time.

---

## 9. Capture, burst, and sound

- **Snapshot:** tap **Capture** when **snapshot** mode is selected in Settings (see **Capture mode** below). With keyboard focus on the main window, **Space** may also trigger capture (deployment build).  
- **Burst:** enable **burst** mode in **Settings**; set **count** and **interval** (seconds). Tap **Capture** to start; tap again to stop early if supported.  
- **Delay:** optional **capture delay** (seconds) in Settings before shutter fires.  
- **Sound:** shutter / UI feedback sound can be **disabled** in Settings (**camera sound** toggle).  

Captured files are written under your configured **capture directory** (local disk or **SD card target** when available). Filenames include **patient ID** when entered.

---

## 10. Patient ID and storage

- **Patient ID:** enter in **Settings**; option **“use last patient ID”** speeds repeat visits.  
- **Storage target:** **System** (PC path, e.g. under user or `DentalImages`) vs **SD card** when a removable volume is detected; UI indicates status.  
- **Low space:** warnings or blocking may apply when free space is below thresholds in **`config/storage_config.json`**.  
- **Export:** **Export all** and **DICOM** actions copy or convert **already captured** images from the session gallery list to a folder you pick (including **network paths** if available in the Windows folder dialog).  

**Network / cloud:** there is no separate “upload to OneDrive” button; saving to a **synced folder** or **mapped drive** is done by choosing that path in the export folder dialog.

---

## 11. Presets

- **Three chips** at the bottom right: **short tap** recalls a preset; **long press** saves current **brightness, zoom, pan**, transforms, and image-setting slider snapshot into that slot (with confirmation feedback).  
- Recalling a preset applies **camera-side exposure/gain** and **LED** level when in AUTO LED mode per your configuration.  

---

## 12. Settings panel

Accessible via the **gear** on the right rail (may require **settings password** — see below).

Typical contents include:

- **Display:** grid overlay, crosshair, auto-scale preview.  
- **Capture:** preview gallery, **export all**, **DICOM** export, patient ID field, **use last ID**, capture **format** (PNG/JPEG), **quality**, **burst** options, **delay**, **camera sound**.  
- **Storage:** **SYSTEM / SD CARD** target selection and status text.  
- **Lock:** close and **lock** settings to require password again.  

Exact labels match the deployed QML build.

---

## 13. Kiosk mode, exit, and passwords

- The window runs **full screen** with **frameless** chrome suitable for kiosk PCs.  
- **Exit application:** attempt to close the window opens the **Admin Exit** password dialog. On keyboards, **Ctrl+Shift+Q** also opens that dialog. Enter the **admin password** to quit.  
- **Open Settings:** the **gear** icon may ask for the **settings** password before the panel opens.

There are **two separate passwords**:

| Role | Environment variable | Default if unset |
|------|----------------------|------------------|
| **Quit / exit the application** | `DENTAL_ADMIN_PASSWORD` | `admin` |
| **Unlock the Settings panel** | `DENTAL_SETTINGS_PASSWORD` | `admin` |

**You should change both before clinical use.** They are not changed from inside the app UI—only via the methods below.

### How to change the passwords

**Method 1 — Edit `RunDentalImaging.bat` (simplest for a dedicated kiosk)**  

1. Open **`RunDentalImaging.bat`** in Notepad (or your editor).  
2. Near the top, **after** the line `cd /d "%~dp0"`, add two lines (use your own secrets):

   ```bat
   set "DENTAL_ADMIN_PASSWORD=YourExitPasswordHere"
   set "DENTAL_SETTINGS_PASSWORD=YourSettingsPasswordHere"
   ```

3. Save the file.  
4. Start the app **only** via this batch file so those values apply.  

**Tips:** Keep the **`set "VAR=value"`** form with quotes if the password contains spaces. Avoid characters that are special in batch files (`&`, `|`, `<`, `>`) unless you know how to escape them. Protect the `.bat` file with **NTFS permissions** so operators cannot read the passwords (e.g. only an admin account can edit it).

---

**Method 2 — Windows user environment variables**  

1. Press **Win**, type **environment variables**, open **Edit the system environment variables** (you may use **Edit environment variables for your account** if you prefer user scope only).  
2. Under **User variables** (or **System variables** for all users), click **New…**.  
   - Variable name: `DENTAL_ADMIN_PASSWORD` — value: your exit password.  
   - Repeat for `DENTAL_SETTINGS_PASSWORD`.  
3. **OK** out of all dialogs.  
4. **Fully close** any running Dental Imaging app, then start it again from a **new** shortcut or **`RunDentalImaging.bat`** so the process picks up the new values. If passwords still look old, **sign out of Windows and sign in** once (environment is loaded at login for programs started from the shell differently in some setups).

---

**Method 3 — One-time launch from Command Prompt**  

```bat
cd /d "C:\path\to\dental_image_system"
set DENTAL_ADMIN_PASSWORD=YourExitPassword
set DENTAL_SETTINGS_PASSWORD=YourSettingsPassword
call venv\Scripts\activate.bat
python app\main.py
```

(Adjust paths if your install layout differs.)

### Other environment variables (optional)

| Variable | Purpose |
|----------|---------|
| **`DENTAL_LED_IDLE_MINUTES`** | Minutes of no video activity before LED **OFF** command (minimum enforced in code may apply). |
| **`DENTAL_IMAGING_ROOT`** | Optional override root to find **`config/`** files. |

---

## 14. Configuration files

All under **`config/`** beside the application:

| File | Purpose |
|------|---------|
| **`default_config.json`** | Application / preview / storage defaults. |
| **`camera_defaults.json`** | Basler resolution, exposure, gain, frame rate seed values on connect. |
| **`storage_config.json`** | Free-space thresholds and related guards. |
| **`led_presets.json`** | LED preset metadata if used. |
| **`presets.json`** | Saved user presets (created after long-press save). |

---

## 15. Troubleshooting

| Symptom |Things to check |
|---------|----------------|
| **Black preview / no camera** | Pylon installed? Camera in Device Manager / pylon Viewer? USB 3.0 port? Tap **power** to connect. |
| **“Industrial camera SDK unavailable”** | Pylon not installed or Python environment missing **pypylon**. Re-run **`RunDentalImaging.bat`**. |
| **LEDs not responding** | ESP32 powered? Correct COM port? Another app using serial? Unplug/replug USB; wait for reconnect. |
| **Capture fails** | Disk space; storage target; patient ID / path characters; see on-screen toast. |
| **Cannot open Settings** | Enter **`DENTAL_SETTINGS_PASSWORD`**. |
| **Cannot exit app** | Enter **`DENTAL_ADMIN_PASSWORD`**. |
| **DICOM export fails** | **pydicom** and **opencv** must be installed (included in `requirements.txt`). |

---

## 16. Appendix A — Requirements implementation checklist

The table below maps the **SOW functional requirements** (`project_requirements.txt`) to behaviour **delivered in this software build**. Use it for **site acceptance**; clinical validation remains the customer’s responsibility.

| # | Requirement area | Delivered capability |
|---|------------------|----------------------|
| **1** | **Camera init & control** | Auto-detect Basler devices via **pypylon**; **Connect / disconnect** (power control); live preview at interactive frame rate; defaults from **`camera_defaults.json`**; **image settings** sliders (hardware exposure/gain + software colour). |
| **2** | **Zoom & ROI** | Digital zoom slider; **pinch** zoom; **pan**; **ROI mode** with diagonal selection and auto zoom/center; physical lens adjusted by operator. |
| **3** | **LED control** | **115200** serial; **`DIM:X`**, **`ON`/`OFF`**, **`STATUS`**; brightness slider + AUTO/OFF/HIGH UI; **idle auto-off**; robust **reconnect** behaviour. |
| **4** | **Capture & saving** | Snapshot + **burst** (count/interval); **PNG/JPEG**; **patient ID** naming; **export** to chosen folder; **DICOM** export path in Settings; **folder dialog** supports local / removable / **network** paths; capture **sound** optional. |
| **5** | **Presets** | **Three** preset buttons; **tap** recall; **long-press** save with feedback; stores brightness, zoom, pan, transforms, image sliders. |
| **6** | **GUI & usability** | Touch-first **PyQt6 + QML** layout; large controls; **fullscreen kiosk**; **password** exit and **password** Settings; **tooltips** on key rail actions. **English** UI. |
| — | **SOW deliverables: source** | **Python 3.10+** source tree with **PyQt6**, **pypylon**, **pyserial**, **opencv-python**, **pydicom**. |
| — | **SOW deliverables: operator launcher** | **`RunDentalImaging.bat`** (source run) or **`DentalImaging.exe`** via **`build_exe.bat`** / **`docs/BUILD_EXE.md`**. |
| — | **SOW deliverables: manual** | **This document** serves as the user manual; export to PDF from Word/Markdown if a signed-off PDF is required. |
| — | **SOW deliverables: formal test report** | Perform **site acceptance** using Appendix A and your clinical test protocol; formal report is a **customer / QA** artefact. |
| — | **Security / HIPAA wording** | **Settings** guarded by password. **Encryption of images** is **not** built into the app; use **OS encryption**, secure shares, and clinic policy for PHI. |
| — | **Performance** | Designed for **up to ~31 fps** sensor class; preview is scaled; tune PC and USB for best results. |

**Firmware:** ESP32 behaviour (closed-loop dim, `ADC` / `RECAL` commands, etc.) is defined in **`firmware/esp32_led_controller/`** and should be flashed to match hardware.

---

## 17. Appendix B — Optional Windows kiosk hardening

For stricter **shell lock-down** (hide Taskbar beyond the app window, dedicated user):

- Consider Windows **Assigned Access** / **kiosk** mode or similar **MDM** policies for the clinical user account.  
- Ensure a maintenance path exists for **Pylon updates** and **Windows patches** (break-glass admin account).  

---

*End of Client User Guide.*
