# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — onedir build (one folder with DentalImaging.exe + _internal).

Build from repository root:
  pyinstaller --noconfirm DentalImaging.spec

Output: dist/DentalImaging/DentalImaging.exe
Ship the whole ``dist/DentalImaging`` folder plus a ``config`` folder beside it (see docs/BUILD_EXE.md).
"""
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.abspath(SPEC)))  # type: ignore[name-defined]

block_cipher = None

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT), str(ROOT / "app")],
    binaries=[],
    datas=[
        (str(ROOT / "app" / "qml"), "app/qml"),
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "camera_core",
        "camera_core.exceptions",
        "camera_core.exceptions.camera_exceptions",
        "camera_core.models",
        "camera_core.models.camera_config",
        "camera_core.utils",
        "camera_core.utils.frame_converter",
        "camera_core.hardware",
        "camera_core.hardware.camera",
        "camera_core.hardware.camera.basler_camera",
        "camera_core.hardware.camera.camera_detection",
        "camera_core.hardware.camera.camera_settings_helper",
        "camera_core.image_processing",
        "camera_core.image_processing.color_adjustments",
        "camera_core.storage",
        "camera_core.storage.snapshot_writer",
        "runtime_paths",
        "bridge",
        "camera_service",
        "provider",
        "serial_service",
        "view_transforms",
        "app_settings",
        "pypylon",
        "cv2",
        "numpy",
        "pydicom",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pandas", "sphinx"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DentalImaging",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DentalImaging",
)
