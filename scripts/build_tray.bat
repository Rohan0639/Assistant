@echo off
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
cd /d "%ROOT_DIR%"

echo Building JARVIS Tray Application...

echo Installing PyInstaller and required packages...
pip install pyinstaller pystray pillow

echo Building executable...
pyinstaller --name "JARVIS" --noconsole --onefile jarvis/tray_app.py

echo Build complete! You can find the executable in the 'dist' folder.
pause
