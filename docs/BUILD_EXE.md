# Building a Windows executable (PyInstaller)

The project includes **`DentalImaging.spec`** for a **folder-style** build (**onedir**): one `DentalImaging.exe` plus an `_internal` folder with libraries. This is more reliable for PyQt6 + QML than a single large **onefile** exe.

## Prerequisites

- Windows **10/11**, **Python 3.10+** with the same packages as development (`pip install -r requirements.txt`).
- **PyInstaller:** `pip install pyinstaller` (also listed under optional dev deps in `requirements-dev.txt`).
- **Basler Pylon** on the build machine if you want to verify the camera at runtime (the built PC still needs Pylon installed to use the camera).

## Build steps

1. Open **Command Prompt** or **PowerShell** and go to the **repository root** (folder that contains `DentalImaging.spec` and `app/`).

2. Install dependencies (use a venv if you prefer):
   ```bat
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. Run PyInstaller:
   ```bat
   pyinstaller --noconfirm DentalImaging.spec
   ```

4. Output layout:
   ```text
   dist\DentalImaging\
     DentalImaging.exe
     _internal\          (DLLs, Python, PyQt6, bundled QML, etc.)
   ```

## What to ship to the client

Copy the **entire** folder:

`dist\DentalImaging\`

**and** place a **`config`** folder **next to** `DentalImaging.exe` (same level as `_internal`), containing your JSON files from the repo:

```text
DentalImaging\
  DentalImaging.exe
  _internal\
  config\
    default_config.json
    camera_defaults.json
    storage_config.json
    led_presets.json
    …
```

The application resolves **`config/`** and **`captures/`** relative to the **`.exe` directory** when frozen (see `app/runtime_paths.py`). Optional: add **`docs/`** and **`RunDentalImaging.bat`** is **not** required for the exe build.

First run will create **`captures`** under that same folder when patients capture images (if your settings use a relative path).

## Optional: `build_exe.bat`

From the repo root, run **`build_exe.bat`** — it installs PyInstaller if needed, runs the spec, and copies **`config`** into **`dist\DentalImaging\config`**.

## Basler / pypylon on the target PC

- Install **Basler Pylon** on every machine that runs the camera.
- If the app fails to load the camera with a DLL error, install the same **Visual C++ Redistributable** Basler/Pylon requires (per Basler’s documentation).

## One-file exe (`--onefile`)

Not recommended for this QML app (slow startup, occasional antivirus false positives). If you need it, add `onefile=True` patterns in PyInstaller docs; you must still ship **`config`** beside the exe or set **`DENTAL_IMAGING_ROOT`**.

## Troubleshooting the build

| Issue | What to try |
|-------|-------------|
| Missing module at runtime | Add the module to `hiddenimports` in `DentalImaging.spec` and rebuild. |
| QML / white window | Ensure `app/qml` is listed in `datas` in the spec (already present). |
| Huge build pulling pytest/pandas | The spec **excludes** some test/doc packages; adjust `excludes` if something needed is stripped. |
