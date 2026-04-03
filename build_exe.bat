@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo Building Dental Imaging exe with PyInstaller...
echo.

where py >nul 2>&1
if errorlevel 1 (set "PY=python") else (set "PY=py -3")

%PY% -c "import PyInstaller" 2>nul
if errorlevel 1 (
  echo Installing PyInstaller...
  %PY% -m pip install "pyinstaller>=6.0"
  if errorlevel 1 (
    echo Failed to install PyInstaller.
    pause
    exit /b 1
  )
)

%PY% -m PyInstaller --noconfirm DentalImaging.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Copying config folder next to the exe...
if exist "dist\DentalImaging\config" (
  echo config already exists in dist\DentalImaging — skipping copy.
) else (
  if exist "config" (
    xcopy /E /I /Y "config" "dist\DentalImaging\config"
  ) else (
    echo WARNING: No config folder in repo root.
  )
)

echo.
echo Done. Run:  dist\DentalImaging\DentalImaging.exe
echo See docs\BUILD_EXE.md for deployment notes.
echo.
pause
