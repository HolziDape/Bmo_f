@echo off
chcp 65001 >nul
color 0A
cls
echo.
echo  ____    __  __    ___
echo ^| __ )  ^|  \/  ^|  / _ \
echo ^|  _ \  ^| ^|\/^| ^| ^| ^| ^| ^|
echo ^| ^|_) ^| ^| ^|  ^| ^| ^| ^|_^| ^|
echo ^|____/  ^|_^|  ^|_^|  \___/
echo.
echo  ========================================
echo   Freund-Version
echo  ========================================
echo.

:: Beim ersten Start Pakete automatisch installieren
python -c "import flask" 2>nul
if errorlevel 1 (
    echo   Erster Start - Pakete werden installiert...
    echo.
    pip install flask flask-cors requests psutil spotipy pillow
    echo.
    echo   [ OK ]  Setup abgeschlossen!
    echo.
)

cd /d "%~dp0"
start "" python bmo_web_freund.py

echo   [ OK ]  BMO laeuft!
echo   [ OK ]  Browser oeffnet sich gleich...
echo.
echo  ========================================
echo   Web: http://localhost:5000
echo  ========================================
echo.
timeout /t 4 /nobreak >nul
