@echo off
echo Building JARVIS Tray Application...

echo Installing PyInstaller and required packages...
pip install pyinstaller pystray pillow

echo Building executable...
pyinstaller --name "JARVIS" --noconsole --onefile jarvis/tray_app.py

echo Build complete! You can find the executable in the 'dist' folder.
pause
