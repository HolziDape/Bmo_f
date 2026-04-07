# BMO Points, Games, Draw & Lite-Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Punkte-System mit Mini-Spielen (Pong Solo, Tetris, Snake, Breakout), Draw-Feature (bidirektional) und Lite-Mode Toggle für den Admin hinzufügen.

**Architecture:** `bmo_points.py` (HMAC-Modul, von bmo_web_freund.py importiert) und `bmo_games.py` (Flask-Blueprint mit Spielen + Session-Management) sind neue Dateien. `bmo_web_freund.py` und `bmo_core.py` bekommen minimale Erweiterungen für Draw-Feature, Punkte-Sync und Lite-Mode.

**Tech Stack:** Python 3, Flask, Flask-CORS, hmac/hashlib (stdlib), tkinter (stdlib), JavaScript Canvas API

---

## Datei-Übersicht

| Datei | Aktion | Inhalt |
|---|---|---|
| `D:\python\scripts\Bmo_f_tmp2\bmo_points.py` | **NEU** | HMAC sign/verify, Feature-Kosten lesen, Admin-Punkte speichern |
| `D:\python\scripts\Bmo_f_tmp2\bmo_games.py` | **NEU** | Flask-Blueprint, Session-Tokens, Plausibilitätsprüfung, Spiel-HTML |
| `D:\python\scripts\Bmo_f_tmp2\tests\test_points.py` | **NEU** | Unit-Tests für bmo_points.py |
| `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py` | **ÄNDERN** | Blueprint registrieren, `/api/points/sync`, `/api/features/use`, Draw-Overlay, Punkte-Header |
| `D:\python\scripts\Bmo_main\src\bmo_core.py` | **ÄNDERN** | Lite-Mode Flag, `/lite-mode`, `/api/points/verify`, Draw-State + Routes |
| `D:\python\scripts\Bmo_main\src\bmo_web.py` | **ÄNDERN** | Lite-Mode Button in quick-btns (Zeile ~1200) |

---

## Task 1: bmo_points.py — HMAC-Modul

**Files:**
- Create: `D:\python\scripts\Bmo_f_tmp2\bmo_points.py`
- Create: `D:\python\scripts\Bmo_f_tmp2\tests\test_points.py`

- [ ] **Step 1: Datei anlegen**

`D:\python\scripts\Bmo_f_tmp2\bmo_points.py`:
```python
"""
bmo_points.py — Punkte-System: HMAC-Signierung, Feature-Kosten, Admin-Sync
"""
import hmac
import hashlib
import json
import os
import secrets

DEFAULT_COSTS = {
    'jumpscare':   50,
    'screen_view': 30,
    'screen_draw': 40,
}

def ensure_secret(config_path: str) -> str:
    """Liest POINTS_SECRET aus config.txt; generiert + speichert falls fehlend."""
    lines = []
    secret = None
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('POINTS_SECRET='):
                secret = line.strip().split('=', 1)[1]
                break
    if not secret:
        secret = secrets.token_hex(32)
        lines.append(f'POINTS_SECRET={secret}\n')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return secret

def sign(points: int, secret: str) -> str:
    """Gibt HMAC-SHA256-Signatur für einen Punkte-Stand zurück."""
    msg = str(int(points)).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

def verify(points: int, sig: str, secret: str) -> bool:
    """Prüft ob die Signatur zum Punkte-Stand passt."""
    expected = sign(points, secret)
    return hmac.compare_digest(expected, sig)

def get_costs(config_path: str) -> dict:
    """Liest COST_* Werte aus config.txt; fällt auf DEFAULT_COSTS zurück."""
    costs = DEFAULT_COSTS.copy()
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                for key in DEFAULT_COSTS:
                    prefix = f'COST_{key.upper()}='
                    if line.startswith(prefix):
                        try:
                            costs[key] = int(line.strip().split('=', 1)[1])
                        except ValueError:
                            pass
    return costs

def save_points_admin(points: int, freund_id: str, data_dir: str) -> None:
    """Speichert verifizierten Punkte-Stand für einen Freund (auf Admin-PC)."""
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, f'points_{freund_id.replace(":", "_").replace(".", "_")}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'points': points, 'freund_id': freund_id}, f)

def load_points_admin(freund_id: str, data_dir: str) -> int:
    """Lädt gespeicherten Punkte-Stand für einen Freund (auf Admin-PC)."""
    path = os.path.join(data_dir, f'points_{freund_id.replace(":", "_").replace(".", "_")}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('points', 0)
    return 0
```

- [ ] **Step 2: Tests schreiben**

`D:\python\scripts\Bmo_f_tmp2\tests\test_points.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tempfile
import bmo_points

def test_sign_verify_valid():
    sig = bmo_points.sign(100, 'secret')
    assert bmo_points.verify(100, sig, 'secret')

def test_verify_wrong_points():
    sig = bmo_points.sign(100, 'secret')
    assert not bmo_points.verify(200, sig, 'secret')

def test_verify_wrong_secret():
    sig = bmo_points.sign(100, 'secret1')
    assert not bmo_points.verify(100, sig, 'secret2')

def test_ensure_secret_creates_and_persists():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write('CORE_IP=100.0.0.1\n')
        path = f.name
    try:
        s1 = bmo_points.ensure_secret(path)
        assert len(s1) == 64
        s2 = bmo_points.ensure_secret(path)
        assert s1 == s2   # zweiter Aufruf gibt gleichen Secret zurück
    finally:
        os.unlink(path)

def test_get_costs_defaults():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write('CORE_IP=100.0.0.1\n')
        path = f.name
    try:
        costs = bmo_points.get_costs(path)
        assert costs == {'jumpscare': 50, 'screen_view': 30, 'screen_draw': 40}
    finally:
        os.unlink(path)

def test_get_costs_custom_override():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write('COST_JUMPSCARE=25\nCOST_SCREEN_VIEW=10\n')
        path = f.name
    try:
        costs = bmo_points.get_costs(path)
        assert costs['jumpscare'] == 25
        assert costs['screen_view'] == 10
        assert costs['screen_draw'] == 40   # unverändert
    finally:
        os.unlink(path)

def test_save_and_load_points_admin():
    with tempfile.TemporaryDirectory() as d:
        bmo_points.save_points_admin(150, '100.64.0.1', d)
        assert bmo_points.load_points_admin('100.64.0.1', d) == 150

def test_load_points_admin_missing_returns_zero():
    with tempfile.TemporaryDirectory() as d:
        assert bmo_points.load_points_admin('nonexistent', d) == 0
```

- [ ] **Step 3: Tests laufen lassen — müssen PASS sein**

```bash
cd D:\python\scripts\Bmo_f_tmp2
python -m pytest tests/test_points.py -v
```
Erwartet: 7x PASSED

- [ ] **Step 4: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_points.py tests/test_points.py
git commit -m "feat: add bmo_points HMAC module with tests"
```

---

## Task 2: Points-Sync Route in bmo_web_freund.py

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py`

- [ ] **Step 1: bmo_points importieren**

Direkt nach den bestehenden Imports (nach `import functools`, ca. Zeile 52) einfügen:
```python
import bmo_points as _bmo_points
```

- [ ] **Step 2: Points-Secret beim Start laden**

Nach der Zeile `cfg = read_config()` (ca. Zeile 133) einfügen:
```python
_CONFIG_TXT = os.path.join(BASE_DIR, "config.txt")
_POINTS_SECRET = _bmo_points.ensure_secret(_CONFIG_TXT)
_DATA_DIR = os.path.join(BASE_DIR, "_intern", "data")
```

- [ ] **Step 3: `/api/points/sync` Route hinzufügen**

Vor der Zeile `@app.route('/jumpscare'` (ca. Zeile 170 im Admin-Block) einfügen:
```python
# ══════════════════════════════════════════════════════════════════
# PUNKTE-SYSTEM
# ══════════════════════════════════════════════════════════════════

@app.route('/api/points/sync', methods=['POST'])
@login_required
def api_points_sync():
    """Empfängt Punkte-Stand vom Browser, verifiziert Signatur, synct mit Admin."""
    data = request.get_json(silent=True) or {}
    client_points = int(data.get('points', 0))
    client_sig    = data.get('sig', '')

    # Lokale Signatur prüfen
    if not _bmo_points.verify(client_points, client_sig, _POINTS_SECRET):
        # Manipulation: auf letzten bekannten Admin-Stand zurücksetzen
        freund_id = _cfg.get('CORE_IP', 'unknown')
        safe_points = _bmo_points.load_points_admin(freund_id, _DATA_DIR)
        new_sig = _bmo_points.sign(safe_points, _POINTS_SECRET)
        return jsonify(points=safe_points, sig=new_sig, reset=True)

    # Punkte auf Admin-PC syncen (falls online)
    freund_id = _cfg.get('CORE_IP', 'unknown')
    if CORE_URL:
        try:
            r = req.post(
                f'{CORE_URL}/api/points/verify',
                json={'points': client_points, 'sig': client_sig, 'freund_id': freund_id},
                timeout=3
            )
            if r.ok:
                admin_data = r.json()
                verified = admin_data.get('points', client_points)
                new_sig = _bmo_points.sign(verified, _POINTS_SECRET)
                return jsonify(points=verified, sig=new_sig)
        except Exception:
            pass  # Admin offline — lokalen Stand behalten

    # Admin offline: lokalen Stand bestätigen
    new_sig = _bmo_points.sign(client_points, _POINTS_SECRET)
    return jsonify(points=client_points, sig=new_sig)


@app.route('/api/features/use', methods=['POST'])
@login_required
def api_features_use():
    """Zieht Punkte für ein Feature ab und löst es beim Admin aus."""
    data    = request.get_json(silent=True) or {}
    feature = data.get('feature', '')
    points  = int(data.get('points', 0))
    sig     = data.get('sig', '')

    if not _bmo_points.verify(points, sig, _POINTS_SECRET):
        return jsonify(error='Ungültige Signatur'), 403

    costs = _bmo_points.get_costs(_CONFIG_TXT)
    cost  = costs.get(feature)
    if cost is None:
        return jsonify(error='Unbekanntes Feature'), 400
    if points < cost:
        return jsonify(error='Nicht genug Punkte'), 402

    new_points = points - cost
    new_sig    = _bmo_points.sign(new_points, _POINTS_SECRET)

    # Feature beim Admin auslösen
    result = 'ok'
    if CORE_URL:
        try:
            if feature == 'jumpscare':
                req.post(f'{CORE_URL}/jumpscare', timeout=3)
            elif feature == 'screen_view':
                pass  # Screen wird client-seitig geöffnet
            elif feature == 'screen_draw':
                req.post(f'{CORE_URL}/api/draw/open', timeout=3)
        except Exception as e:
            result = f'Feature-Fehler: {e}'

    # Neuen Stand auf Admin sichern
    freund_id = _cfg.get('CORE_IP', 'unknown')
    if CORE_URL:
        try:
            req.post(
                f'{CORE_URL}/api/points/verify',
                json={'points': new_points, 'sig': new_sig, 'freund_id': freund_id},
                timeout=3
            )
        except Exception:
            pass

    return jsonify(points=new_points, sig=new_sig, result=result)
```

- [ ] **Step 4: Server starten und manuell testen**

```bash
cd D:\python\scripts\Bmo_f_tmp2
python bmo_web_freund.py
```
Im Browser: `http://localhost:5001` aufrufen, einloggen.  
In einer anderen Terminal-Session:
```bash
python -c "
import requests, bmo_points
secret = bmo_points.ensure_secret('D:/python/scripts/Bmo_f_tmp2/config.txt')
sig = bmo_points.sign(100, secret)
r = requests.post('http://localhost:5001/api/points/sync', json={'points':100,'sig':sig}, cookies={'session': 'HIER_SESSION_COOKIE'})
print(r.json())
"
```
Erwartet: `{'points': 100, 'sig': '...', 'reset': False}` (oder ohne `reset` key wenn Admin offline)

- [ ] **Step 5: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_web_freund.py
git commit -m "feat: add points sync and feature-use routes to bmo_web_freund"
```

---

## Task 3: Points-Verify Endpunkt in bmo_core.py (Admin)

**Files:**
- Modify: `D:\python\scripts\Bmo_main\src\bmo_core.py`

- [ ] **Step 1: bmo_points-äquivalente Logik importieren**

Direkt nach `import threading` (ca. Zeile 50) einfügen:
```python
import hmac as _hmac
import hashlib as _hashlib
import secrets as _secrets
```

- [ ] **Step 2: Points-Konfiguration laden**

Nach `CONVERSATIONS_PATH = ...` (ca. Zeile 78) einfügen:
```python
BMO_CONFIG_PATH = os.path.join(BASE_DIR, "_intern", "bmo_config.txt")
DATA_DIR        = os.path.join(BASE_DIR, "_intern", "data")

def _read_bmo_config() -> dict:
    cfg = {}
    if os.path.exists(BMO_CONFIG_PATH):
        with open(BMO_CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    cfg[k.strip()] = v.strip()
    return cfg

def _write_bmo_config(cfg: dict):
    with open(BMO_CONFIG_PATH, 'w', encoding='utf-8') as f:
        for k, v in cfg.items():
            f.write(f'{k}={v}\n')

def _ensure_points_secret() -> str:
    cfg = _read_bmo_config()
    if 'POINTS_SECRET' not in cfg:
        cfg['POINTS_SECRET'] = _secrets.token_hex(32)
        _write_bmo_config(cfg)
    return cfg['POINTS_SECRET']

_POINTS_SECRET_ADMIN = _ensure_points_secret()

def _points_sign(points: int) -> str:
    return _hmac.new(_POINTS_SECRET_ADMIN.encode(), str(int(points)).encode(), _hashlib.sha256).hexdigest()

def _points_verify(points: int, sig: str) -> bool:
    return _hmac.compare_digest(_points_sign(points), sig)

def _save_points(points: int, freund_id: str):
    import json
    os.makedirs(DATA_DIR, exist_ok=True)
    safe_id = freund_id.replace(':', '_').replace('.', '_')
    with open(os.path.join(DATA_DIR, f'points_{safe_id}.json'), 'w', encoding='utf-8') as f:
        json.dump({'points': points, 'freund_id': freund_id}, f)

def _load_points(freund_id: str) -> int:
    import json
    safe_id = freund_id.replace(':', '_').replace('.', '_')
    path = os.path.join(DATA_DIR, f'points_{safe_id}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('points', 0)
    return 0
```

- [ ] **Step 3: `/api/points/verify` Route hinzufügen**

Nach `@app.route('/ping'` Block (ca. Zeile 924) einfügen:
```python
@app.route('/api/points/verify', methods=['POST'])
def route_points_verify():
    """Empfängt und verifiziert Punkte-Stand vom Freund-Server."""
    data      = request.get_json(silent=True) or {}
    points    = int(data.get('points', 0))
    freund_id = data.get('freund_id', 'unknown')

    stored = _load_points(freund_id)
    # Erlaubt: Stand stimmt mit gespeichertem überein oder ist höher (Punkte verdient)
    # Ablehnen: Stand ist niedriger als gespeichert (hätte schon abgezogen sein müssen)
    if points < stored:
        # Manipulation: gespeicherten Stand zurückspielen
        return jsonify(points=stored, corrected=True)

    _save_points(points, freund_id)
    return jsonify(points=points, corrected=False)
```

- [ ] **Step 4: Server starten und testen**

```bash
cd D:\python\scripts\Bmo_main\src
python bmo_core.py
```
In anderer Terminal:
```bash
python -c "
import requests
r = requests.post('http://localhost:6000/api/points/verify', json={'points': 100, 'freund_id': '100.64.0.1'})
print(r.json())  # erwartet: {'points': 100, 'corrected': False}
r2 = requests.post('http://localhost:6000/api/points/verify', json={'points': 50, 'freund_id': '100.64.0.1'})
print(r2.json()) # erwartet: {'points': 100, 'corrected': True}  (Manipulation erkannt)
"
```

- [ ] **Step 5: Commit**

```bash
cd D:\python\scripts\Bmo_main
git add src/bmo_core.py
git commit -m "feat: add points verify endpoint and config helpers to bmo_core"
```

---

## Task 4: Punkte-Anzeige im Frontend (bmo_web_freund.py)

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py`

- [ ] **Step 1: Punkte-Badge im Header hinzufügen**

Den bestehenden `<header>` Block (enthält `coreDot`, `h1`, `coreStatus`) um ein Punkte-Badge erweitern. Die Zeile mit `<h1>BMO</h1>` finden und den Header-Block so ändern:

Vorher (ca. Zeile 739):
```html
  <header>
    <div class="dot" id="coreDot"></div>
    <div>
      <h1>BMO</h1>
      <span class="sub" id="coreStatus">Verbinde...</span>
    </div>
  </header>
```
Nachher:
```html
  <header>
    <div class="dot" id="coreDot"></div>
    <div>
      <h1>BMO</h1>
      <span class="sub" id="coreStatus">Verbinde...</span>
    </div>
    <div id="pointsBadge" style="margin-left:auto;background:rgba(34,197,94,0.12);border:1px solid #22c55e;border-radius:20px;padding:4px 12px;font-size:13px;font-weight:700;color:#4ade80;cursor:pointer;" onclick="showPointsShop()">
      ⭐ <span id="pointsVal">0</span>
    </div>
  </header>
```

- [ ] **Step 2: Punkte-Shop Overlay HTML hinzufügen**

Nach dem letzten Overlay-Block am Ende des HTML-Body (vor `</body>`) einfügen:
```html
<!-- PUNKTE-SHOP OVERLAY -->
<div class="overlay" id="pointsOverlay" onclick="closeOverlay('pointsOverlay')">
  <div class="sheet" onclick="event.stopPropagation()">
    <div class="sheet-handle"></div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="margin:0;">⭐ Punkte-Shop</h2>
      <span style="font-size:22px;font-weight:700;color:#4ade80;" id="shopPoints">0 Pkt</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px;">
      <button class="shop-btn" onclick="buyFeature('jumpscare')" data-cost="50">
        <span>👻 Jumpscare beim Admin</span><span class="shop-cost" id="cost_jumpscare">50 ⭐</span>
      </button>
      <button class="shop-btn" onclick="buyFeature('screen_view')" data-cost="30">
        <span>🖥️ Admin-Screen ansehen</span><span class="shop-cost" id="cost_screen_view">30 ⭐</span>
      </button>
      <button class="shop-btn" onclick="buyFeature('screen_draw')" data-cost="40">
        <span>🎨 Auf Admin-Screen malen</span><span class="shop-cost" id="cost_screen_draw">40 ⭐</span>
      </button>
    </div>
    <div style="margin-top:16px;font-size:12px;color:var(--text2);text-align:center;">
      Spiele Spiele um Punkte zu verdienen!
    </div>
  </div>
</div>
```

- [ ] **Step 3: CSS für Shop-Buttons im `<style>` Block hinzufügen**

Im `<style>`-Block (vor `</style>`) einfügen:
```css
.shop-btn { display:flex; justify-content:space-between; align-items:center; padding:14px 16px; background:var(--bg3); border:1px solid var(--border); border-radius:14px; color:var(--text); font-size:15px; cursor:pointer; transition:background .15s; width:100%; }
.shop-btn:active { background:var(--border); }
.shop-cost { font-weight:700; color:#4ade80; font-size:14px; }
```

- [ ] **Step 4: Punkte-JavaScript hinzufügen**

Im `<script>`-Block am Anfang der JS-Sektion einfügen:
```javascript
// ── PUNKTE ────────────────────────────────────────────────────────
let _pts = 0, _ptsSig = '';

function _loadPoints() {
  try {
    const d = JSON.parse(localStorage.getItem('bmo_points') || '{}');
    _pts = d.points || 0; _ptsSig = d.sig || '';
  } catch(e) { _pts = 0; _ptsSig = ''; }
  _updatePointsUI();
}

function _savePoints(p, s) {
  _pts = p; _ptsSig = s;
  localStorage.setItem('bmo_points', JSON.stringify({points: p, sig: s}));
  _updatePointsUI();
}

function _updatePointsUI() {
  document.getElementById('pointsVal').textContent = _pts;
  document.getElementById('shopPoints').textContent = _pts + ' Pkt';
}

async function syncPoints() {
  if (!_ptsSig) return;
  try {
    const r = await fetch('/api/points/sync', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({points:_pts, sig:_ptsSig})});
    const d = await r.json();
    _savePoints(d.points, d.sig);
  } catch(e) {}
}

function showPointsShop() {
  document.getElementById('pointsOverlay').classList.add('show');
}

async function buyFeature(feature) {
  const r = await fetch('/api/features/use', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({feature, points:_pts, sig:_ptsSig})});
  const d = await r.json();
  if (d.error) { alert(d.error); return; }
  _savePoints(d.points, d.sig);
  if (feature === 'screen_draw') { closeOverlay('pointsOverlay'); openAdminDraw(); }
  if (feature === 'screen_view') { closeOverlay('pointsOverlay'); showMyScreen(); }
}

// Beim Start: laden und syncen
_loadPoints();
setTimeout(syncPoints, 2000);
```

- [ ] **Step 5: Testen**

Server starten (`python bmo_web_freund.py`), im Browser aufrufen. Badge `⭐ 0` sollte im Header erscheinen. Badge anklicken → Shop öffnet sich.

- [ ] **Step 6: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_web_freund.py
git commit -m "feat: add points badge, shop overlay and sync JS to frontend"
```

---

## Task 5: bmo_games.py — Blueprint + Session-Management

**Files:**
- Create: `D:\python\scripts\Bmo_f_tmp2\bmo_games.py`

- [ ] **Step 1: Blueprint-Grundgerüst anlegen**

`D:\python\scripts\Bmo_f_tmp2\bmo_games.py`:
```python
"""
bmo_games.py — Mini-Spiele Blueprint (Pong Solo, Tetris, Snake, Breakout)
Wird in bmo_web_freund.py registriert.
"""
import time
import secrets
import threading
from flask import Blueprint, request, jsonify, render_template_string

games_bp = Blueprint('games', __name__)

# Aktive Spiel-Sessions: {token: {'game': str, 'start': float}}
_sessions: dict = {}
_sessions_lock  = threading.Lock()

# Minimale Spielzeit in Sekunden (Anti-Cheat)
MIN_GAME_SECONDS = {
    'pong':     60,
    'tetris':   60,
    'snake':    30,
    'breakout': 20,
}

GAME_POINTS = {
    'pong':     30,
    'tetris':   25,
    'snake':    20,
    'breakout': 15,
}

@games_bp.route('/games/<game>')
def game_page(game):
    if game not in MIN_GAME_SECONDS:
        return 'Spiel nicht gefunden', 404
    token = secrets.token_hex(16)
    with _sessions_lock:
        _sessions[token] = {'game': game, 'start': time.time()}
    # Alte Sessions aufräumen (>2h)
    _cleanup_sessions()
    return render_template_string(_GAME_PAGES[game], token=token, points=GAME_POINTS[game])

def _cleanup_sessions():
    cutoff = time.time() - 7200
    with _sessions_lock:
        expired = [t for t, s in _sessions.items() if s['start'] < cutoff]
        for t in expired:
            del _sessions[t]
```

- [ ] **Step 2: `/api/games/complete` Route hinzufügen**

An bmo_games.py anhängen:
```python
@games_bp.route('/api/games/complete', methods=['POST'])
def api_games_complete():
    """Verifiziert Spiel-Ergebnis und gibt neue Punkte zurück."""
    # Import hier um Zirkulärimport zu vermeiden
    import bmo_points as _bp
    from flask import current_app

    data  = request.get_json(silent=True) or {}
    token = data.get('token', '')
    game  = data.get('game', '')

    with _sessions_lock:
        session = _sessions.pop(token, None)

    if not session:
        return jsonify(error='Ungültige Session'), 403
    if session['game'] != game:
        return jsonify(error='Falsches Spiel'), 403

    elapsed = time.time() - session['start']
    min_sec = MIN_GAME_SECONDS.get(game, 30)
    if elapsed < min_sec:
        return jsonify(error=f'Zu schnell ({elapsed:.0f}s < {min_sec}s)'), 403

    # Punkte aus localStorage auf Frontend-Seite kommen via body
    current_points = int(data.get('points', 0))
    current_sig    = data.get('sig', '')

    config_path = current_app.config.get('CONFIG_TXT', 'config.txt')
    secret      = current_app.config.get('POINTS_SECRET', '')

    if not _bp.verify(current_points, current_sig, secret):
        return jsonify(error='Ungültige Signatur'), 403

    earned     = GAME_POINTS[game]
    new_points = current_points + earned
    new_sig    = _bp.sign(new_points, secret)

    return jsonify(points=new_points, sig=new_sig, earned=earned)
```

- [ ] **Step 3: Blueprint in bmo_web_freund.py registrieren**

Nach `app = Flask(__name__)` und `CORS(app)` (ca. Zeile 68) einfügen:
```python
from bmo_games import games_bp
app.register_blueprint(games_bp)
```

Und nach `_POINTS_SECRET = _bmo_points.ensure_secret(_CONFIG_TXT)` einfügen:
```python
app.config['CONFIG_TXT']     = _CONFIG_TXT
app.config['POINTS_SECRET']  = _POINTS_SECRET
```

- [ ] **Step 4: Platzhalter für Game-Pages einfügen**

An bmo_games.py anhängen:
```python
# Wird in Tasks 6-9 gefüllt
_GAME_PAGES: dict = {}
```

- [ ] **Step 5: Server testen**

```bash
cd D:\python\scripts\Bmo_f_tmp2
python bmo_web_freund.py
```
Im Browser: `http://localhost:5001/games/pong` aufrufen.  
Erwartet: `404 Spiel nicht gefunden` (weil _GAME_PAGES noch leer ist — wird in Task 6 gefüllt)  
Aber kein Python-Fehler beim Start = Blueprint korrekt registriert.

- [ ] **Step 6: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_games.py bmo_web_freund.py
git commit -m "feat: add games blueprint with session management"
```

---

## Task 6: Pong Solo-Modus

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_games.py`

- [ ] **Step 1: Pong-HTML in _GAME_PAGES einfügen**

`_GAME_PAGES: dict = {}` ersetzen durch:
```python
_GAME_PAGES: dict = {
    'pong': _PONG_HTML,
    'tetris': '',
    'snake': '',
    'breakout': '',
}
```

Und VOR `_GAME_PAGES` die Konstante einfügen:
```python
_PONG_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMO Pong</title>
<style>
  body{margin:0;background:#0f172a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100dvh;font-family:sans-serif;color:#e2e8f0;}
  canvas{border:2px solid #22c55e;border-radius:4px;touch-action:none;}
  #msg{font-size:18px;margin-top:16px;min-height:24px;color:#4ade80;}
  #info{font-size:14px;color:#64748b;margin-top:8px;}
</style>
</head>
<body>
<h2 style="color:#4ade80;margin-bottom:8px;">🏓 BMO Pong Solo</h2>
<div id="info">Gewinne 10 Runden → +{{ points }} ⭐</div>
<canvas id="c" width="420" height="260"></canvas>
<div id="msg">Bereit! Bewege die Maus oder tippe auf den Bildschirm.</div>
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const W=canvas.width,H=canvas.height,PW=10,PH=60,BALL=8,SPEED=4;
let py=(H-PH)/2,ay=(H-PH)/2,bx=W/2,by=H/2,vx=SPEED,vy=SPEED*(Math.random()>.5?1:-1);
let wins=0,losses=0,running=true,gameOver=false;

canvas.addEventListener('mousemove',e=>{
  const r=canvas.getBoundingClientRect();
  py=Math.min(H-PH,Math.max(0,e.clientY-r.top-PH/2));
});
canvas.addEventListener('touchmove',e=>{
  e.preventDefault();
  const r=canvas.getBoundingClientRect();
  py=Math.min(H-PH,Math.max(0,e.touches[0].clientY-r.top-PH/2));
},{passive:false});

function resetBall(dir){
  bx=W/2;by=H/2;
  vx=(SPEED+wins*0.15)*(dir||1);
  vy=(SPEED+wins*0.1)*(Math.random()>.5?1:-1);
}

function draw(){
  ctx.fillStyle='#0f172a';ctx.fillRect(0,0,W,H);
  // Mittellinie
  ctx.setLineDash([8,8]);ctx.strokeStyle='#1e293b';ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);ctx.stroke();
  ctx.setLineDash([]);
  // Score
  ctx.fillStyle='#334155';ctx.font='bold 32px sans-serif';ctx.textAlign='center';
  ctx.fillText(wins,W/4,40);ctx.fillText(losses,3*W/4,40);
  ctx.fillStyle='#64748b';ctx.font='12px sans-serif';
  ctx.fillText('Wins',W/4,58);ctx.fillText('Verloren',3*W/4,58);
  // Paddles
  ctx.fillStyle='#22c55e';ctx.beginPath();
  ctx.roundRect(4,py,PW,PH,4);ctx.fill();
  ctx.fillStyle='#ef4444';ctx.beginPath();
  ctx.roundRect(W-PW-4,ay,PW,PH,4);ctx.fill();
  // Ball
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(bx,by,BALL,0,Math.PI*2);ctx.fill();
}

function loop(){
  if(!running)return;
  // AI
  const aim=by-(PH/2);
  ay+=(aim-ay)*0.1;
  ay=Math.max(0,Math.min(H-PH,ay));
  // Ball move
  bx+=vx;by+=vy;
  // Wall bounce
  if(by-BALL<0){by=BALL;vy*=-1;}
  if(by+BALL>H){by=H-BALL;vy*=-1;}
  // Player paddle
  if(bx-BALL<PW+4&&by>py&&by<py+PH){bx=PW+4+BALL;vx=Math.abs(vx)*(1+0.05*wins);vy+=(by-(py+PH/2))*0.1;}
  // AI paddle
  if(bx+BALL>W-PW-4&&by>ay&&by<ay+PH){bx=W-PW-4-BALL;vx=-Math.abs(vx)*(1+0.05*wins);}
  // Score
  if(bx<0){losses++;document.getElementById('msg').textContent=`Verloren! ${wins}/10 Wins`;resetBall(1);}
  if(bx>W){wins++;document.getElementById('msg').textContent=wins<10?`Gewonnen! ${wins}/10 Wins`:' ';resetBall(-1);}
  draw();
  if(wins>=10&&!gameOver){gameOver=true;running=false;finish();}
  else requestAnimationFrame(loop);
}

async function finish(){
  document.getElementById('msg').textContent='10 Wins! Punkte werden gutgeschrieben...';
  const stored=JSON.parse(localStorage.getItem('bmo_points')||'{}');
  const r=await fetch('/api/games/complete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({token:'{{ token }}',game:'pong',points:stored.points||0,sig:stored.sig||''})});
  const d=await r.json();
  if(d.error){document.getElementById('msg').textContent='Fehler: '+d.error;return;}
  localStorage.setItem('bmo_points',JSON.stringify({points:d.points,sig:d.sig}));
  document.getElementById('msg').textContent=`+${d.earned} ⭐ → jetzt ${d.points} Punkte! Fenster schließen.`;
}

resetBall();loop();
</script>
</body>
</html>"""
```

- [ ] **Step 2: Testen**

```bash
cd D:\python\scripts\Bmo_f_tmp2
python bmo_web_freund.py
```
Browser: `http://localhost:5001/games/pong` — Pong-Spiel muss erscheinen und spielbar sein (Maus bewegt linkes Paddle).

- [ ] **Step 3: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_games.py
git commit -m "feat: add Pong solo game with AI opponent"
```

---

## Task 7: Tetris

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_games.py`

- [ ] **Step 1: `'tetris': ''` in _GAME_PAGES durch `_TETRIS_HTML` ersetzen und Konstante einfügen**

VOR `_GAME_PAGES` einfügen:
```python
_TETRIS_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMO Tetris</title>
<style>
  body{margin:0;background:#0f172a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100dvh;font-family:sans-serif;color:#e2e8f0;}
  canvas{border:2px solid #a855f7;border-radius:4px;}
  #msg{font-size:16px;margin-top:12px;min-height:20px;color:#c084fc;}
  .ctrl{display:flex;gap:8px;margin-top:12px;}
  .ctrl button{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:10px 18px;border-radius:10px;font-size:18px;cursor:pointer;}
</style>
</head>
<body>
<h2 style="color:#c084fc;margin-bottom:4px;">🟣 BMO Tetris</h2>
<div style="font-size:13px;color:#64748b;margin-bottom:8px;">Level 5 erreichen → +{{ points }} ⭐</div>
<canvas id="c" width="200" height="400"></canvas>
<div id="msg">← → bewegen | ↑ drehen | ↓ fallen</div>
<div class="ctrl">
  <button ontouchstart="move(-1)">◀</button>
  <button ontouchstart="rotate()">🔄</button>
  <button ontouchstart="move(1)">▶</button>
  <button ontouchstart="drop()">▼</button>
</div>
<script>
const COLS=10,ROWS=20,SZ=20;
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const PIECES=[
  {s:[[1,1,1,1]],c:'#22d3ee'},
  {s:[[1,0],[1,0],[1,1]],c:'#f97316'},
  {s:[[0,1],[0,1],[1,1]],c:'#3b82f6'},
  {s:[[1,1],[1,1]],c:'#facc15'},
  {s:[[0,1,1],[1,1,0]],c:'#22c55e'},
  {s:[[1,1,0],[0,1,1]],c:'#ef4444'},
  {s:[[1,1,1],[0,1,0]],c:'#a855f7'},
];
let board=Array.from({length:ROWS},()=>Array(COLS).fill(0));
let cur,cx,cy,score=0,level=1,lines=0,gameOver=false,done=false;

function newPiece(){
  const p=PIECES[Math.floor(Math.random()*PIECES.length)];
  cur={s:p.s.map(r=>[...r]),c:p.c};
  cx=Math.floor((COLS-cur.s[0].length)/2);cy=0;
  if(!fits(cur.s,cx,cy)){gameOver=true;document.getElementById('msg').textContent='Game Over!';}
}

function fits(s,x,y){
  for(let r=0;r<s.length;r++)for(let c=0;c<s[r].length;c++)
    if(s[r][c]&&(y+r>=ROWS||x+c<0||x+c>=COLS||board[y+r][x+c]))return false;
  return true;
}

function place(){
  cur.s.forEach((r,ri)=>r.forEach((v,ci)=>{if(v)board[cy+ri][cx+ci]=cur.c;}));
  let cleared=0;
  board=board.filter(r=>{if(r.every(c=>c)){cleared++;return false;}return true;});
  while(board.length<ROWS)board.unshift(Array(COLS).fill(0));
  lines+=cleared;score+=cleared*100;
  level=Math.floor(lines/10)+1;
  document.getElementById('msg').textContent=`Level ${level} | Zeilen ${lines} | Score ${score}`;
  if(level>=5&&!done){done=true;finish();return;}
  newPiece();
}

function move(d){if(!gameOver&&!done&&fits(cur.s,cx+d,cy))cx+=d;}
function drop(){if(!gameOver&&!done&&fits(cur.s,cx,cy+1))cy++;else if(!gameOver&&!done)place();}
function rotate(){
  if(gameOver||done)return;
  const r=cur.s[0].map((_,i)=>cur.s.map(row=>row[i]).reverse());
  if(fits(r,cx,cy))cur.s=r;
}

document.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft')move(-1);
  if(e.key==='ArrowRight')move(1);
  if(e.key==='ArrowDown')drop();
  if(e.key==='ArrowUp')rotate();
});

function draw(){
  ctx.fillStyle='#0f172a';ctx.fillRect(0,0,200,400);
  ctx.strokeStyle='#1e293b';ctx.lineWidth=0.5;
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    const v=board[r][c];
    ctx.fillStyle=v||'#0f172a';
    ctx.fillRect(c*SZ,r*SZ,SZ-1,SZ-1);
  }
  if(cur)cur.s.forEach((r,ri)=>r.forEach((v,ci)=>{
    if(v){ctx.fillStyle=cur.c;ctx.fillRect((cx+ci)*SZ,(cy+ri)*SZ,SZ-1,SZ-1);}
  }));
}

let last=0,interval=600;
function loop(ts){
  if(gameOver||done)return;
  if(ts-last>Math.max(100,interval-level*50)){last=ts;drop();}
  draw();requestAnimationFrame(loop);
}

async function finish(){
  document.getElementById('msg').textContent='Level 5! Punkte werden gutgeschrieben...';
  const stored=JSON.parse(localStorage.getItem('bmo_points')||'{}');
  const r=await fetch('/api/games/complete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({token:'{{ token }}',game:'tetris',points:stored.points||0,sig:stored.sig||''})});
  const d=await r.json();
  if(d.error){document.getElementById('msg').textContent='Fehler: '+d.error;return;}
  localStorage.setItem('bmo_points',JSON.stringify({points:d.points,sig:d.sig}));
  document.getElementById('msg').textContent=`+${d.earned} ⭐ → jetzt ${d.points} Punkte!`;
}

newPiece();
document.getElementById('msg').textContent=`Level ${level} | Zeilen ${lines} | Score ${score}`;
requestAnimationFrame(loop);
</script>
</body>
</html>"""
```

In `_GAME_PAGES` `'tetris': ''` durch `'tetris': _TETRIS_HTML` ersetzen.

- [ ] **Step 2: Testen**

`http://localhost:5001/games/tetris` — Tetris muss erscheinen und spielbar sein. Pfeiltasten bewegen/drehen.

- [ ] **Step 3: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_games.py
git commit -m "feat: add Tetris game"
```

---

## Task 8: Snake

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_games.py`

- [ ] **Step 1: `_SNAKE_HTML` einfügen und `_GAME_PAGES` aktualisieren**

VOR `_GAME_PAGES` einfügen:
```python
_SNAKE_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMO Snake</title>
<style>
  body{margin:0;background:#0f172a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100dvh;font-family:sans-serif;color:#e2e8f0;}
  canvas{border:2px solid #22c55e;border-radius:4px;}
  #msg{font-size:16px;margin-top:12px;min-height:20px;color:#4ade80;}
  .ctrl{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px;width:150px;}
  .ctrl button{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:12px;border-radius:10px;font-size:18px;cursor:pointer;}
</style>
</head>
<body>
<h2 style="color:#4ade80;margin-bottom:4px;">🐍 BMO Snake</h2>
<div style="font-size:13px;color:#64748b;margin-bottom:8px;">20 Äpfel essen → +{{ points }} ⭐</div>
<canvas id="c" width="300" height="300"></canvas>
<div id="msg">WASD oder Pfeiltasten</div>
<div class="ctrl">
  <div></div><button ontouchstart="setDir(0,-1)">▲</button><div></div>
  <button ontouchstart="setDir(-1,0)">◀</button>
  <button ontouchstart="setDir(0,1)">▼</button>
  <button ontouchstart="setDir(1,0)">▶</button>
</div>
<script>
const SZ=20,COLS=15,ROWS=15;
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let snake=[{x:7,y:7}],dir={x:1,y:0},nextDir={x:1,y:0};
let apple={x:3,y:3},eaten=0,dead=false,done=false;

function randApple(){
  let a;
  do{a={x:Math.floor(Math.random()*COLS),y:Math.floor(Math.random()*ROWS)};}
  while(snake.some(s=>s.x===a.x&&s.y===a.y));
  apple=a;
}

function setDir(x,y){if(snake.length>1&&x===-dir.x&&y===-dir.y)return;nextDir={x,y};}
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft'||e.key==='a')setDir(-1,0);
  if(e.key==='ArrowRight'||e.key==='d')setDir(1,0);
  if(e.key==='ArrowUp'||e.key==='w')setDir(0,-1);
  if(e.key==='ArrowDown'||e.key==='s')setDir(0,1);
});

function step(){
  if(dead||done)return;
  dir=nextDir;
  const head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
  if(head.x<0||head.x>=COLS||head.y<0||head.y>=ROWS||snake.some(s=>s.x===head.x&&s.y===head.y)){
    dead=true;document.getElementById('msg').textContent='Kollision! Seite neu laden zum Weiterspielen.';return;
  }
  snake.unshift(head);
  if(head.x===apple.x&&head.y===apple.y){
    eaten++;document.getElementById('msg').textContent=`${eaten}/20 Äpfel`;
    randApple();
    if(eaten>=20){done=true;finish();}
  } else {
    snake.pop();
  }
}

function draw(){
  ctx.fillStyle='#0f172a';ctx.fillRect(0,0,300,300);
  ctx.fillStyle='#ef4444';ctx.fillRect(apple.x*SZ+2,apple.y*SZ+2,SZ-4,SZ-4);
  snake.forEach((s,i)=>{
    ctx.fillStyle=i===0?'#4ade80':'#22c55e';
    ctx.fillRect(s.x*SZ+1,s.y*SZ+1,SZ-2,SZ-2);
  });
}

async function finish(){
  document.getElementById('msg').textContent='20 Äpfel! Punkte werden gutgeschrieben...';
  const stored=JSON.parse(localStorage.getItem('bmo_points')||'{}');
  const r=await fetch('/api/games/complete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({token:'{{ token }}',game:'snake',points:stored.points||0,sig:stored.sig||''})});
  const d=await r.json();
  if(d.error){document.getElementById('msg').textContent='Fehler: '+d.error;return;}
  localStorage.setItem('bmo_points',JSON.stringify({points:d.points,sig:d.sig}));
  document.getElementById('msg').textContent=`+${d.earned} ⭐ → jetzt ${d.points} Punkte!`;
}

randApple();
setInterval(()=>{step();draw();},150);
</script>
</body>
</html>"""
```

In `_GAME_PAGES` `'snake': ''` durch `'snake': _SNAKE_HTML` ersetzen.

- [ ] **Step 2: Testen**

`http://localhost:5001/games/snake` — Snake muss erscheinen, WASD funktionieren, Apfel gegessen werden können.

- [ ] **Step 3: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_games.py
git commit -m "feat: add Snake game"
```

---

## Task 9: Breakout

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_games.py`

- [ ] **Step 1: `_BREAKOUT_HTML` einfügen und `_GAME_PAGES` aktualisieren**

VOR `_GAME_PAGES` einfügen:
```python
_BREAKOUT_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMO Breakout</title>
<style>
  body{margin:0;background:#0f172a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100dvh;font-family:sans-serif;color:#e2e8f0;}
  canvas{border:2px solid #38bdf8;border-radius:4px;touch-action:none;}
  #msg{font-size:16px;margin-top:12px;min-height:20px;color:#38bdf8;}
</style>
</head>
<body>
<h2 style="color:#38bdf8;margin-bottom:4px;">🧱 BMO Breakout</h2>
<div style="font-size:13px;color:#64748b;margin-bottom:8px;">Alle Steine zerstören → +{{ points }} ⭐</div>
<canvas id="c" width="400" height="300"></canvas>
<div id="msg">Maus/Touch bewegt Paddle</div>
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const W=400,H=300,PW=70,PH=10,BALL=7,BROWS=4,BCOLS=8;
const BCOLORS=['#ef4444','#f97316','#facc15','#22c55e'];
let px=(W-PW)/2,bx=W/2,by=H-40,vx=3,vy=-4;
let bricks=[],lives=3,done=false;

for(let r=0;r<BROWS;r++)for(let c=0;c<BCOLS;c++)
  bricks.push({x:c*48+8,y:r*22+30,w:44,h:18,alive:true,c:BCOLORS[r]});

canvas.addEventListener('mousemove',e=>{const r=canvas.getBoundingClientRect();px=Math.min(W-PW,Math.max(0,e.clientX-r.left-PW/2));});
canvas.addEventListener('touchmove',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();px=Math.min(W-PW,Math.max(0,e.touches[0].clientX-r.left-PW/2));},{passive:false});

function draw(){
  ctx.fillStyle='#0f172a';ctx.fillRect(0,0,W,H);
  // Bricks
  bricks.forEach(b=>{if(!b.alive)return;ctx.fillStyle=b.c;ctx.beginPath();ctx.roundRect(b.x,b.y,b.w,b.h,3);ctx.fill();});
  // Paddle
  ctx.fillStyle='#38bdf8';ctx.beginPath();ctx.roundRect(px,H-PH-5,PW,PH,5);ctx.fill();
  // Ball
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(bx,by,BALL,0,Math.PI*2);ctx.fill();
  // Lives
  ctx.fillStyle='#ef4444';ctx.font='14px sans-serif';ctx.textAlign='left';
  ctx.fillText('❤️'.repeat(lives),8,16);
}

function loop(){
  if(done)return;
  bx+=vx;by+=vy;
  if(bx-BALL<0){bx=BALL;vx*=-1;}
  if(bx+BALL>W){bx=W-BALL;vx*=-1;}
  if(by-BALL<0){by=BALL;vy*=-1;}
  if(by+BALL>H-PH-5&&bx>px&&bx<px+PW&&vy>0){
    vy*=-1;vx+=(bx-(px+PW/2))*0.05;
  }
  if(by>H){
    lives--;
    if(lives<=0){document.getElementById('msg').textContent='Game Over! Seite neu laden.';return;}
    bx=W/2;by=H-40;vx=3;vy=-4;
  }
  bricks.forEach(b=>{
    if(!b.alive)return;
    if(bx+BALL>b.x&&bx-BALL<b.x+b.w&&by+BALL>b.y&&by-BALL<b.y+b.h){
      b.alive=false;vy*=-1;
    }
  });
  const alive=bricks.filter(b=>b.alive).length;
  if(alive===0&&!done){done=true;finish();return;}
  draw();requestAnimationFrame(loop);
}

async function finish(){
  document.getElementById('msg').textContent='Alle Steine! Punkte werden gutgeschrieben...';
  const stored=JSON.parse(localStorage.getItem('bmo_points')||'{}');
  const r=await fetch('/api/games/complete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({token:'{{ token }}',game:'breakout',points:stored.points||0,sig:stored.sig||''})});
  const d=await r.json();
  if(d.error){document.getElementById('msg').textContent='Fehler: '+d.error;return;}
  localStorage.setItem('bmo_points',JSON.stringify({points:d.points,sig:d.sig}));
  document.getElementById('msg').textContent=`+${d.earned} ⭐ → jetzt ${d.points} Punkte!`;
}

draw();requestAnimationFrame(loop);
</script>
</body>
</html>"""
```

In `_GAME_PAGES` `'breakout': ''` durch `'breakout': _BREAKOUT_HTML` ersetzen.

- [ ] **Step 2: Testen**

`http://localhost:5001/games/breakout` — Breakout muss erscheinen, Paddle per Maus steuerbar, Bälle prallen von Steinen ab.

- [ ] **Step 3: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_games.py
git commit -m "feat: add Breakout game"
```

---

## Task 10: Spiel-Buttons in der Haupt-UI

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py`

- [ ] **Step 1: Spiele-Overlay HTML hinzufügen**

Nach dem Punkte-Shop Overlay (aus Task 4) einfügen:
```html
<!-- SPIELE OVERLAY -->
<div class="overlay" id="gamesOverlay" onclick="closeOverlay('gamesOverlay')">
  <div class="sheet" onclick="event.stopPropagation()">
    <div class="sheet-handle"></div>
    <h2 style="margin-bottom:16px;">🎮 Spiele</h2>
    <div style="display:flex;flex-direction:column;gap:10px;">
      <button class="shop-btn" onclick="openGame('pong')">
        <span>🏓 Pong Solo</span><span style="color:#4ade80;font-size:13px;">+30 ⭐ bei 10 Wins</span>
      </button>
      <button class="shop-btn" onclick="openGame('tetris')">
        <span>🟣 Tetris</span><span style="color:#c084fc;font-size:13px;">+25 ⭐ bei Level 5</span>
      </button>
      <button class="shop-btn" onclick="openGame('snake')">
        <span>🐍 Snake</span><span style="color:#4ade80;font-size:13px;">+20 ⭐ bei 20 Äpfeln</span>
      </button>
      <button class="shop-btn" onclick="openGame('breakout')">
        <span>🧱 Breakout</span><span style="color:#38bdf8;font-size:13px;">+15 ⭐ bei Stage Clear</span>
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Spiele-Button in quick-btns hinzufügen**

Im `<div class="quick-btns">` Block nach dem Pong-Button (ca. Zeile 758) einfügen:
```html
    <button class="qbtn" onclick="closeOverlay('pongOverlay');document.getElementById('gamesOverlay').classList.add('show')" style="border-color:#f59e0b;color:#fbbf24;">
      <span class="icon">🎮</span>Spiele
    </button>
```

- [ ] **Step 3: `openGame()` Funktion im JavaScript hinzufügen**

Im `<script>`-Block einfügen:
```javascript
function openGame(name) {
  closeOverlay('gamesOverlay');
  window.open('/games/' + name, '_blank');
}
```

- [ ] **Step 4: Nach Rückkehr vom Spiel Punkte neu laden**

In der `syncPoints()` Funktion (aus Task 4) nach `_savePoints(d.points, d.sig)` sicherstellen dass das localStorage beim Fokus aktualisiert wird. Im Script-Block einfügen:
```javascript
window.addEventListener('focus', () => {
  _loadPoints();
  setTimeout(syncPoints, 500);
});
```

- [ ] **Step 5: Testen**

Browser: Spiele-Button klicken → Overlay mit 4 Spielen erscheint. Tetris anklicken → neuer Tab öffnet sich mit Tetris-Spiel.

- [ ] **Step 6: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_web_freund.py
git commit -m "feat: add games overlay and buttons to main UI"
```

---

## Task 11: Draw-Feature — Admin-Seite (bmo_core.py)

**Files:**
- Modify: `D:\python\scripts\Bmo_main\src\bmo_core.py`

- [ ] **Step 1: Draw-State hinzufügen**

Nach `_POINTS_SECRET_ADMIN = _ensure_points_secret()` (aus Task 3) einfügen:
```python
# ── DRAW STATE ──────────────────────────────────────────────────────────────
_draw_strokes_for_friend: list = []   # Admin → Freund Striche
_draw_strokes_from_friend: list = []  # Freund → Admin Striche (für tkinter)
_draw_lock = threading.Lock()
_draw_window_open = False
```

- [ ] **Step 2: Draw-Routen hinzufügen**

Nach `route_points_verify()` (aus Task 3) einfügen:
```python
@app.route('/api/draw/open', methods=['POST'])
def route_draw_open():
    """Freund hat screen_draw gekauft — öffnet tkinter-Canvas auf Admin-Monitor."""
    global _draw_window_open, _draw_strokes_from_friend
    with _draw_lock:
        _draw_strokes_from_friend = []
        _draw_window_open = True
    threading.Thread(target=_run_draw_window, daemon=True).start()
    return jsonify(ok=True)

@app.route('/api/draw/stroke', methods=['POST'])
def route_draw_stroke():
    """Empfängt Strich vom Freund → Admin-tkinter rendert ihn."""
    data = request.get_json(silent=True) or {}
    with _draw_lock:
        if _draw_window_open:
            _draw_strokes_from_friend.append(data)
    return jsonify(ok=True)

@app.route('/api/draw/strokes', methods=['GET'])
def route_draw_strokes():
    """Freund pollt Admin-Striche (Admin→Freund Richtung)."""
    with _draw_lock:
        strokes = list(_draw_strokes_for_friend)
        _draw_strokes_for_friend.clear()
    return jsonify(strokes=strokes)

@app.route('/api/draw/friend-stroke', methods=['POST'])
def route_draw_friend_stroke():
    """Admin sendet Strich an Freund-Browser."""
    data = request.get_json(silent=True) or {}
    with _draw_lock:
        _draw_strokes_for_friend.append(data)
    return jsonify(ok=True)

@app.route('/api/draw/close', methods=['POST'])
def route_draw_close():
    """Schließt Draw-Session."""
    global _draw_window_open
    with _draw_lock:
        _draw_window_open = False
        _draw_strokes_from_friend.clear()
        _draw_strokes_for_friend.clear()
    return jsonify(ok=True)
```

- [ ] **Step 3: tkinter Draw-Fenster Funktion hinzufügen**

Nach den Draw-Routen einfügen:
```python
def _run_draw_window():
    """Öffnet transparentes tkinter-Overlay auf dem Admin-Monitor (Freund malt drauf)."""
    global _draw_window_open
    try:
        import tkinter as tk
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.attributes('-alpha', 0.7)
        root.configure(bg='black')
        root.overrideredirect(True)

        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        lbl = tk.Label(root, text='🎨 Freund malt... (Klick zum Schließen)',
                       bg='black', fg='#4ade80', font=('Arial', 14))
        lbl.place(x=10, y=10)

        def close(_=None):
            global _draw_window_open
            _draw_window_open = False
            root.destroy()

        root.bind('<Button-1>', close)
        root.bind('<Escape>', close)
        root.after(60000, close)  # Auto-close nach 60s

        last_x = last_y = None

        def poll_strokes():
            nonlocal last_x, last_y
            with _draw_lock:
                strokes = list(_draw_strokes_from_friend)
                _draw_strokes_from_friend.clear()
            for s in strokes:
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                x = int(s.get('x', 0) * sw)
                y = int(s.get('y', 0) * sh)
                if s.get('type') == 'move' and last_x is not None:
                    canvas.create_line(last_x, last_y, x, y,
                                       fill=s.get('color', '#ef4444'),
                                       width=int(s.get('w', 4)),
                                       smooth=True, capstyle='round')
                last_x, last_y = x, y
                if s.get('type') == 'up':
                    last_x = last_y = None
            if not _draw_window_open:
                root.destroy()
                return
            root.after(100, poll_strokes)

        root.after(100, poll_strokes)
        root.mainloop()
    except Exception as e:
        log.error(f'Draw-Fenster Fehler: {e}')
    finally:
        _draw_window_open = False
```

- [ ] **Step 4: Testen**

```bash
cd D:\python\scripts\Bmo_main\src
python bmo_core.py
```
```bash
python -c "
import requests
r = requests.post('http://localhost:6000/api/draw/open')
print(r.json())  # Erwartet: {'ok': True}, tkinter-Fenster öffnet sich auf Monitor
"
```

- [ ] **Step 5: Commit**

```bash
cd D:\python\scripts\Bmo_main
git add src/bmo_core.py
git commit -m "feat: add draw endpoints and tkinter overlay to bmo_core"
```

---

## Task 12: Draw-Feature — Freund-Seite (bmo_web_freund.py)

**Files:**
- Modify: `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py`

- [ ] **Step 1: Draw-Overlay HTML hinzufügen**

Nach dem Spiele-Overlay (aus Task 10) einfügen:
```html
<!-- DRAW OVERLAY (Freund malt auf Admin-Screen) -->
<div id="drawOverlay" style="display:none;position:fixed;inset:0;z-index:8000;background:rgba(0,0,0,0.85);flex-direction:column;align-items:center;justify-content:center;">
  <div style="color:#4ade80;font-size:16px;margin-bottom:8px;">🎨 Male auf dem Admin-Bildschirm</div>
  <canvas id="drawCanvas" style="border:2px solid #22c55e;border-radius:8px;cursor:crosshair;touch-action:none;background:#111;"></canvas>
  <div style="display:flex;gap:8px;margin-top:12px;">
    <button onclick="setDrawColor('#ef4444')" style="width:32px;height:32px;background:#ef4444;border:none;border-radius:50%;cursor:pointer;"></button>
    <button onclick="setDrawColor('#22c55e')" style="width:32px;height:32px;background:#22c55e;border:none;border-radius:50%;cursor:pointer;"></button>
    <button onclick="setDrawColor('#38bdf8')" style="width:32px;height:32px;background:#38bdf8;border:none;border-radius:50%;cursor:pointer;"></button>
    <button onclick="setDrawColor('#facc15')" style="width:32px;height:32px;background:#facc15;border:none;border-radius:50%;cursor:pointer;"></button>
    <button onclick="setDrawColor('#fff')" style="width:32px;height:32px;background:#fff;border:none;border-radius:50%;cursor:pointer;"></button>
    <button onclick="closeAdminDraw()" style="background:#1e293b;border:1px solid #475569;color:#e2e8f0;padding:8px 16px;border-radius:10px;cursor:pointer;">✕ Schließen</button>
  </div>
</div>

<!-- FRIEND DRAW OVERLAY (Admin malt auf Freund-Screen) -->
<div id="friendDrawOverlay" style="display:none;position:fixed;inset:0;z-index:7000;pointer-events:none;">
  <canvas id="friendDrawCanvas" style="position:absolute;inset:0;width:100%;height:100%;"></canvas>
  <button onclick="closeFriendDraw()" style="position:absolute;top:10px;right:10px;pointer-events:all;background:#0f172a;border:1px solid #475569;color:#e2e8f0;padding:8px 14px;border-radius:10px;cursor:pointer;z-index:7001;">✕</button>
</div>
```

- [ ] **Step 2: Draw-JavaScript hinzufügen**

Im `<script>`-Block einfügen:
```javascript
// ── DRAW: FREUND MALT AUF ADMIN-SCREEN ────────────────────────────
let _drawColor = '#ef4444', _drawing = false;

function openAdminDraw() {
  const ov = document.getElementById('drawOverlay');
  const cv = document.getElementById('drawCanvas');
  cv.width  = Math.min(window.innerWidth - 32, 380);
  cv.height = Math.min(window.innerHeight - 160, 320);
  ov.style.display = 'flex';

  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#111'; ctx.fillRect(0, 0, cv.width, cv.height);

  function send(type, e) {
    const r = cv.getBoundingClientRect();
    const cx = e.clientX ?? e.touches[0].clientX;
    const cy2 = e.clientY ?? e.touches[0].clientY;
    fetch('/api/draw/stroke-relay', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        type, x: (cx - r.left) / r.width, y: (cy2 - r.top) / r.height,
        color: _drawColor, w: 4
      })
    });
  }

  cv.onmousedown  = e => { _drawing = true; send('down', e); };
  cv.onmousemove  = e => { if(_drawing){ ctx.strokeStyle=_drawColor; ctx.lineWidth=4; const r=cv.getBoundingClientRect(); if(!cv._lx){cv._lx=e.clientX-r.left;cv._ly=e.clientY-r.top;} ctx.beginPath(); ctx.moveTo(cv._lx,cv._ly); cv._lx=e.clientX-r.left; cv._ly=e.clientY-r.top; ctx.lineTo(cv._lx,cv._ly); ctx.stroke(); send('move', e); } };
  cv.onmouseup    = e => { _drawing = false; cv._lx=null; send('up', e); };
  cv.ontouchstart = e => { e.preventDefault(); _drawing = true; send('down', e.touches[0]); };
  cv.ontouchmove  = e => { e.preventDefault(); if(_drawing){ ctx.strokeStyle=_drawColor; ctx.lineWidth=4; const r=cv.getBoundingClientRect(); const t=e.touches[0]; if(!cv._lx){cv._lx=t.clientX-r.left;cv._ly=t.clientY-r.top;} ctx.beginPath(); ctx.moveTo(cv._lx,cv._ly); cv._lx=t.clientX-r.left; cv._ly=t.clientY-r.top; ctx.lineTo(cv._lx,cv._ly); ctx.stroke(); send('move', {clientX:t.clientX,clientY:t.clientY}); } };
  cv.ontouchend   = e => { _drawing = false; cv._lx=null; send('up', {clientX:0,clientY:0}); };
}

function closeAdminDraw() {
  document.getElementById('drawOverlay').style.display = 'none';
  fetch('/api/draw/close-relay', {method: 'POST'});
}

function setDrawColor(c) { _drawColor = c; }

// ── DRAW: ADMIN MALT AUF FREUND-SCREEN ────────────────────────────
let _friendDrawInterval = null;

function startFriendDrawPoll() {
  if (_friendDrawInterval) return;
  const cv = document.getElementById('friendDrawCanvas');
  cv.width = window.innerWidth; cv.height = window.innerHeight;
  const ctx = cv.getContext('2d');
  let lx = null, ly = null;

  _friendDrawInterval = setInterval(async () => {
    try {
      const r = await fetch('/api/draw/friend-strokes');
      const d = await r.json();
      if (!d.strokes || d.strokes.length === 0) return;
      document.getElementById('friendDrawOverlay').style.display = 'block';
      d.strokes.forEach(s => {
        const x = s.x * cv.width, y = s.y * cv.height;
        if (s.type === 'move' && lx !== null) {
          ctx.strokeStyle = s.color || '#ef4444';
          ctx.lineWidth = s.w || 4;
          ctx.lineCap = 'round';
          ctx.beginPath(); ctx.moveTo(lx, ly); ctx.lineTo(x, y); ctx.stroke();
        }
        lx = x; ly = y;
        if (s.type === 'up') { lx = null; ly = null; }
      });
    } catch(e) {}
  }, 300);
}

function closeFriendDraw() {
  document.getElementById('friendDrawOverlay').style.display = 'none';
  const cv = document.getElementById('friendDrawCanvas');
  cv.getContext('2d').clearRect(0, 0, cv.width, cv.height);
}

// Polling beim Start aktivieren
setTimeout(startFriendDrawPoll, 3000);
```

- [ ] **Step 3: Relay-Routes in bmo_web_freund.py hinzufügen**

Im Python-Teil (nach den Points-Routen) einfügen:
```python
@app.route('/api/draw/stroke-relay', methods=['POST'])
@login_required
def api_draw_stroke_relay():
    """Leitet Strich-Daten vom Browser an Admin-Core weiter."""
    data = request.get_json(silent=True) or {}
    if CORE_URL:
        try:
            req.post(f'{CORE_URL}/api/draw/stroke', json=data, timeout=1)
        except Exception:
            pass
    return jsonify(ok=True)

@app.route('/api/draw/friend-strokes', methods=['GET'])
@login_required
def api_draw_friend_strokes():
    """Pollt Admin-Striche für den Freund-Browser."""
    if not CORE_URL:
        return jsonify(strokes=[])
    try:
        r = req.get(f'{CORE_URL}/api/draw/strokes', timeout=2)
        return jsonify(strokes=r.json().get('strokes', []))
    except Exception:
        return jsonify(strokes=[])

@app.route('/api/draw/close-relay', methods=['POST'])
@login_required
def api_draw_close_relay():
    """Schließt Draw-Session auf Admin-Core."""
    if CORE_URL:
        try:
            req.post(f'{CORE_URL}/api/draw/close', timeout=2)
        except Exception:
            pass
    return jsonify(ok=True)
```

- [ ] **Step 4: Testen**

Server starten. Im Shop "Auf Admin-Screen malen" kaufen (braucht 40 Punkte). Draw-Canvas öffnet sich, Malen → Admin-tkinter-Fenster zeigt Striche.

- [ ] **Step 5: Commit**

```bash
cd D:\python\scripts\Bmo_f_tmp2
git add bmo_web_freund.py
git commit -m "feat: add bidirectional draw overlays and relay routes"
```

---

## Task 13: Lite-Mode — bmo_core.py

**Files:**
- Modify: `D:\python\scripts\Bmo_main\src\bmo_core.py`

- [ ] **Step 1: Lite-Mode Flag beim Start lesen**

Die `_read_bmo_config()` Funktion existiert bereits (Task 3). Nach `_POINTS_SECRET_ADMIN = _ensure_points_secret()` einfügen:
```python
LITE_MODE = _read_bmo_config().get('LITE_MODE', 'false').lower() == 'true'
if LITE_MODE:
    log.info("LITE-MODE aktiv — Ollama, TTS und Wake-Word deaktiviert.")
```

- [ ] **Step 2: Ollama-Import und Warmup konditionieren**

Die Zeile `import ollama` (Zeile 44) ersetzen durch:
```python
try:
    import ollama as _ollama_lib
except ImportError:
    _ollama_lib = None
```

Überall wo `ollama.chat(` steht (Zeilen ~573, ~854, ~934), durch `_ollama_lib.chat(` ersetzen. Sicherstellen dass ein Guard davor ist:
```python
if _ollama_lib is None:
    return jsonify(response="KI nicht verfügbar (Lite-Mode)."), 503
```
Das `route_process()` (Zeile 665) und `route_transcribe()` (Zeile 678) und `route_photo()` (Zeile 845) jeweils am Anfang:
```python
if LITE_MODE or _ollama_lib is None:
    return jsonify(response="KI nicht verfügbar im Lite-Mode."), 503
```

- [ ] **Step 3: `_warmup_ollama()` konditionieren**

Im `if __name__ == '__main__':` Block (Zeile 939) die Warmup-Zeile einschließen:
```python
if not LITE_MODE:
    threading.Thread(target=_warmup_ollama, daemon=True).start()
```

- [ ] **Step 4: `/lite-mode` Toggle-Route hinzufügen**

Nach `route_draw_close()` einfügen:
```python
@app.route('/lite-mode', methods=['POST'])
def route_lite_mode():
    """Schaltet Lite-Mode ein/aus (erfordert Neustart zum Übernehmen)."""
    global LITE_MODE
    data = request.get_json(silent=True) or {}
    enable = data.get('enable', not LITE_MODE)
    cfg = _read_bmo_config()
    cfg['LITE_MODE'] = 'true' if enable else 'false'
    _write_bmo_config(cfg)
    LITE_MODE = enable
    log.info(f"Lite-Mode {'aktiviert' if enable else 'deaktiviert'}. Neustart empfohlen.")
    return jsonify(lite_mode=enable, restart_required=True)

@app.route('/lite-mode', methods=['GET'])
def route_lite_mode_get():
    return jsonify(lite_mode=LITE_MODE)
```

- [ ] **Step 5: Testen — Lite-Mode an**

```bash
python -c "
import requests
r = requests.post('http://localhost:6000/lite-mode', json={'enable': True})
print(r.json())  # {'lite_mode': True, 'restart_required': True}
r2 = requests.get('http://localhost:6000/lite-mode')
print(r2.json()) # {'lite_mode': True}
"
```

Dann bmo_core.py neu starten — `import ollama` darf keinen Fehler werfen wenn Ollama nicht läuft.

- [ ] **Step 6: Commit**

```bash
cd D:\python\scripts\Bmo_main
git add src/bmo_core.py
git commit -m "feat: add lite-mode flag, conditional ollama init and toggle route"
```

---

## Task 14: Lite-Mode — Admin-UI Toggle (bmo_web.py)

**Files:**
- Modify: `D:\python\scripts\Bmo_main\src\bmo_web.py`

- [ ] **Step 1: Lite-Mode Button in quick-btns einfügen**

Im `<div class="quick-btns">` Block (nach Zeile 1199, nach dem Spiele-Button) einfügen:
```html
    <button class="qbtn" id="liteModeBtn" onclick="toggleLiteMode()" style="border-color:#475569;color:#94a3b8;">
      <span class="icon">⚡</span>Lite
    </button>
```

- [ ] **Step 2: Lite-Mode JavaScript hinzufügen**

Im `<script>`-Block einfügen:
```javascript
// ── LITE-MODE ──────────────────────────────────────────────────────
async function loadLiteMode() {
  try {
    const r = await fetch('/api/lite-mode');
    const d = await r.json();
    updateLiteBtn(d.lite_mode);
  } catch(e) {}
}

function updateLiteBtn(on) {
  const btn = document.getElementById('liteModeBtn');
  if (!btn) return;
  btn.style.borderColor = on ? '#22c55e' : '#475569';
  btn.style.color       = on ? '#4ade80' : '#94a3b8';
  btn.style.background  = on ? 'rgba(34,197,94,0.08)' : '';
  btn.querySelector('.icon').textContent = on ? '⚡' : '⚡';
}

async function toggleLiteMode() {
  try {
    const r = await fetch('/api/lite-mode');
    const cur = (await r.json()).lite_mode;
    const r2 = await fetch('/api/lite-mode/set', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({enable: !cur})
    });
    const d = await r2.json();
    updateLiteBtn(d.lite_mode);
    if (d.restart_required) {
      alert(`Lite-Mode ${d.lite_mode ? 'aktiviert' : 'deaktiviert'}. BMO Core neu starten damit Änderung greift.`);
    }
  } catch(e) { alert('Fehler: Core erreichbar?'); }
}

loadLiteMode();
```

- [ ] **Step 3: Proxy-Routes für Lite-Mode in bmo_web.py hinzufügen**

Im Python-Teil von bmo_web.py, nach den bestehenden Routen (suche nach dem letzten `@app.route`) einfügen:
```python
@app.route('/api/lite-mode', methods=['GET'])
@login_required
def api_lite_mode_get():
    """Gibt aktuellen Lite-Mode Status vom Core zurück."""
    import requests as _req
    try:
        r = _req.get(f'{CORE_URL}/lite-mode', timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify(lite_mode=False, error='Core nicht erreichbar')

@app.route('/api/lite-mode/set', methods=['POST'])
@login_required
def api_lite_mode_set():
    """Setzt Lite-Mode auf Core."""
    import requests as _req
    data = request.get_json(silent=True) or {}
    try:
        r = _req.post(f'{CORE_URL}/lite-mode', json=data, timeout=3)
        return jsonify(r.json())
    except Exception:
        return jsonify(error='Core nicht erreichbar'), 503
```

Hinweis: `CORE_URL` in bmo_web.py ermitteln. Suche nach wo bmo_web.py die Core-IP kennt. Falls noch nicht als Variable vorhanden:
```python
_core_ip_for_web = _cfg.get('CORE_IP', '127.0.0.1')
CORE_URL = f'http://{_core_ip_for_web}:6000'
```

- [ ] **Step 4: Testen**

bmo_web.py starten (`python bmo_web.py`). Im Browser: Lite-Button erscheint in quick-btns. Klick → Toggle-Alert erscheint.

- [ ] **Step 5: Commit**

```bash
cd D:\python\scripts\Bmo_main
git add src/bmo_web.py
git commit -m "feat: add lite-mode toggle button and proxy routes to admin UI"
```

---

## Self-Review gegen Spec

| Spec-Anforderung | Task |
|---|---|
| HMAC-Signierung mit POINTS_SECRET | Task 1, 2, 3 |
| Punkte lokal + sync zu Admin | Task 2, 3 |
| Manipulation → Reset auf letzten bekannten Stand | Task 2 (sync), Task 3 (verify) |
| Pong Solo (10 Wins = 30 Pkt) | Task 6, 10 |
| Tetris (Level 5 = 25 Pkt) | Task 7, 10 |
| Snake (20 Äpfel = 20 Pkt) | Task 8, 10 |
| Breakout (Stage clear = 15 Pkt) | Task 9, 10 |
| Anti-Cheat Session-Token + Plausibilitätscheck | Task 5 |
| Feature-Kosten anpassbar (COST_* in config.txt) | Task 1 |
| Jumpscare kaufen → beim Admin auslösen | Task 2 (features/use) |
| Admin-Screen ansehen (kaufen) | Task 2 (features/use) |
| Freund malt auf Admin-Screen | Task 11, 12 |
| Admin malt auf Freund-Screen | Task 11, 12 |
| Lite-Mode Toggle im Admin-Web | Task 13, 14 |
| Lite-Mode → kein Ollama/TTS/WakeWord | Task 13 |
| Punkte-Anzeige im Header | Task 4 |
| Punkte-Shop Overlay | Task 4 |
