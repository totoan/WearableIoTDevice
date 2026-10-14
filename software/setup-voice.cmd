@echo off
setlocal
set "VOICE_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%VOICE_PYTHON%" (
    py -3.12 -m venv "%~dp0.venv"
    if errorlevel 1 exit /b 1
)
"%VOICE_PYTHON%" -m pip install -r "%~dp0Wearable\requirements.txt"
if errorlevel 1 exit /b 1
"%VOICE_PYTHON%" "%~dp0Wearable\utils\setup_speech.py"
exit /b %errorlevel%
