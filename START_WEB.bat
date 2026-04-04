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

python bmo_web_freund.py

echo.
echo  BMO wurde beendet.
pause
