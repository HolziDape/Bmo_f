# BMO Freund Installer
# Aufruf: powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/HolziDape/Bmo_f/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"

function Write-Header($text) {
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host "   $text" -ForegroundColor Cyan
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-OK($text)   { Write-Host "  [OK] $text" -ForegroundColor Green }
function Write-Info($text) { Write-Host "  --> $text" -ForegroundColor Yellow }
function Write-Err($text)  { Write-Host "  [FEHLER] $text" -ForegroundColor Red }

Clear-Host
Write-Host ""
Write-Host "   ____    __  __    ___  " -ForegroundColor Green
Write-Host "  | __ )  |  \/  |  / _ \ " -ForegroundColor Green
Write-Host "  |  _ \  | |\/| | | | | |" -ForegroundColor Green
Write-Host "  | |_) | | |  | | | |_| |" -ForegroundColor Green
Write-Host "  |____/  |_|  |_|  \___/ " -ForegroundColor Green
Write-Host ""
Write-Host "  BMO Installer — Freundes-Version" -ForegroundColor White
Write-Host ""

# ── 1. Python prüfen / installieren ──────────────────────────────────────────
Write-Header "Schritt 1: Python"

$pythonOk = $false
try {
    $ver = & python --version 2>&1
    if ($ver -match "Python 3\.(\d+)") {
        $minor = [int]$Matches[1]
        if ($minor -ge 10) {
            Write-OK "Python $ver gefunden"
            $pythonOk = $true
        } else {
            Write-Info "Python $ver ist zu alt (mind. 3.10 noetig)"
        }
    }
} catch {}

if (-not $pythonOk) {
    Write-Info "Python wird installiert (winget)..."
    try {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-OK "Python installiert!"
    } catch {
        Write-Err "winget fehlgeschlagen. Bitte Python manuell installieren:"
        Write-Host "     https://python.org/downloads/" -ForegroundColor White
        Write-Host "     Wichtig: Haken bei 'Add Python to PATH' setzen!" -ForegroundColor Yellow
        Read-Host "  Danach ENTER druecken um fortzufahren"
    }
}

# ── 2. Git prüfen / installieren ─────────────────────────────────────────────
Write-Header "Schritt 2: Git"

$gitOk = $false
try {
    $gitVer = & git --version 2>&1
    Write-OK "Git gefunden: $gitVer"
    $gitOk = $true
} catch {}

if (-not $gitOk) {
    Write-Info "Git wird installiert (winget)..."
    try {
        winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-OK "Git installiert!"
    } catch {
        Write-Err "winget fehlgeschlagen. Bitte Git manuell installieren:"
        Write-Host "     https://git-scm.com" -ForegroundColor White
        Read-Host "  Danach ENTER druecken"
    }
}

# ── 3. Repo klonen ────────────────────────────────────────────────────────────
Write-Header "Schritt 3: BMO-Freund herunterladen"

$defaultDir = Join-Path $HOME "BMO_Freund"
Write-Host "  Wo soll BMO-Freund installiert werden?" -ForegroundColor White
Write-Host "  [ENTER druecken fuer Standard: $defaultDir]" -ForegroundColor DarkGray
$userInput = Read-Host "  Pfad"
if ([string]::IsNullOrWhiteSpace($userInput)) {
    $installDir = $defaultDir
} else {
    $installDir = $userInput.Trim('"').Trim("'")
}
Write-OK "Installiere nach: $installDir"

if ((Test-Path $installDir) -and (Test-Path (Join-Path $installDir ".git"))) {
    Write-Info "BMO bereits installiert — wird aktualisiert (git pull)..."
    Set-Location $installDir
    & git pull
} else {
    Write-Info "Klone nach $installDir ..."
    & git clone https://github.com/HolziDape/Bmo_f.git $installDir
    Set-Location $installDir
}
Write-OK "Dateien bereit in $installDir"

# ── 4. Python-Pakete installieren ─────────────────────────────────────────────
Write-Header "Schritt 4: Python-Pakete installieren"

& python -m pip install --upgrade pip | Out-Null
& python -m pip install flask flask-cors requests psutil mss Pillow winotify

Write-OK "Alle Pakete installiert!"

# ── Fertig ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Green
Write-Host "   FERTIG! BMO-Freund ist installiert." -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Naechste Schritte:" -ForegroundColor White
Write-Host "   1. Ordner oeffnen: $installDir" -ForegroundColor White
Write-Host "   2. Doppelklick auf 'START_WEB.bat'" -ForegroundColor White
Write-Host "   3. Browser oeffnet sich auf http://localhost:5000/setup" -ForegroundColor White
Write-Host "   4. Tailscale-IP deines Freundes + Passwort eingeben" -ForegroundColor White
Write-Host ""
Write-Host "  Kein Tailscale? -> https://tailscale.com (kostenlos)" -ForegroundColor Yellow
Write-Host ""

# Explorer oeffnen
Start-Process explorer.exe $installDir
Read-Host "  ENTER zum Beenden"
