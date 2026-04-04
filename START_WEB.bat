@echo off
title BMO Web (Freund)
color 0A
cd /d "%~dp0"
echo.
echo  Starte BMO Web-Interface (Freund-Version)...
echo  Der Browser oeffnet sich automatisch!
echo.
echo  (Fenster nicht schliessen solange BMO laufen soll)
echo.

:: Python suchen und starten
where python >nul 2>&1
if %errorlevel% equ 0 (
    python bmo_web_freund.py
) else (
    echo FEHLER: Python nicht gefunden!
    echo Bitte SETUP_EINMALIG.bat nochmal ausfuehren.
    pause
    exit /b 1
)

echo.
echo  BMO wurde beendet.
pause
