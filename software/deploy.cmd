@echo off
setlocal
rem Python handles export paths and scp arguments without PowerShell.
py -3.12 "%~dp0tools\deploy.py" %*
exit /b %errorlevel%
