@echo off
setlocal EnableExtensions
title Dental Imaging System

REM Always run from the folder where this .bat lives (repo root).
cd /d "%~dp0"

echo.
echo ========================================
echo   Dental Imaging System - Launcher
echo ========================================
echo.

REM --- Pick Python: Windows launcher first, then python on PATH ---
set "PYARGS=-3"
where py >nul 2>&1
if errorlevel 1 (
  set "PYEXE=python"
  set "PYARGS="
) else (
  set "PYEXE=py"
)

%PYEXE% %PYARGS% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if errorlevel 1 (
  echo [ERROR] Python 3.10 or newer is required.
  echo Install from https://www.python.org/downloads/
  echo On the installer, enable "Add python.exe to PATH", then run this file again.
  echo.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo Creating virtual environment in .\venv ...
  %PYEXE% %PYARGS% -m venv venv
  if errorlevel 1 (
    echo [ERROR] Could not create venv. Try: %PYEXE% %PYARGS% -m pip install --user virtualenv
    pause
    exit /b 1
  )
)

call "venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate venv.
  pause
  exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [WARN] pip upgrade failed; continuing anyway.
)

echo Installing Python packages ^(this may take a minute^)...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Package install failed. Check the messages above.
  pause
  exit /b 1
)

echo.
echo NOTE: The Basler Pylon camera driver/SDK must be installed on this PC separately.
echo       https://www.baslerweb.com/en/products/software/basler-pylon-camera-software-suite/
echo.
echo Starting application...
echo.

python app\main.py
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
  echo.
  echo Application closed with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
