@echo off
setlocal
set "PREVIEW_PYTHON=%~dp0.venv\Scripts\python.exe"
if not "%~1"=="" if /I not "%~1"=="--fullscreen" (
    echo Usage: preview.cmd [--fullscreen]
    exit /b 2
)
if not "%~2"=="" (
    echo Usage: preview.cmd [--fullscreen]
    exit /b 2
)
if not exist "%PREVIEW_PYTHON%" (
    py -3.12 -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo Could not create the Python 3.12 environment.
        exit /b 1
    )
)
"%PREVIEW_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    "%PREVIEW_PYTHON%" -m ensurepip --upgrade
    if errorlevel 1 exit /b 1
)
"%PREVIEW_PYTHON%" -c "from PySide6 import QtWidgets, QtWebSockets; import sounddevice, vosk" >nul 2>&1
if errorlevel 1 (
    "%PREVIEW_PYTHON%" -m pip install -r "%~dp0Wearable\requirements.txt"
    if errorlevel 1 exit /b 1
)
if /I "%~1"=="--fullscreen" (
    "%PREVIEW_PYTHON%" "%~dp0Wearable\main.py" --fullscreen
) else (
    "%PREVIEW_PYTHON%" "%~dp0Wearable\main.py"
)
exit /b %errorlevel%
