# Design: PWA (Progressive Web App) für BMO Admin + Freund

**Datum:** 2026-04-08  
**Projekte:** BMO-Main (`bmo_web.py`) + BMO-F (`bmo_web_freund.py`)  
**Status:** Approved

---

## Ziel

Beide Web-Apps sollen auf Handy und PC als echte App installierbar sein ("Zum Startbildschirm hinzufügen" / Browser-Installieren-Prompt).

---

## Status quo

| Feature | bmo_web.py (Admin) | bmo_web_freund.py (Freund) |
|---|---|---|
| `<link rel="manifest">` | ✅ vorhanden | ❌ fehlt |
| `/manifest.json` Route | ✅ vorhanden | ❌ fehlt |
| `/icon.svg` Route + BMO_SVG | ✅ vorhanden | ❌ fehlt |
| Meta-Tags (theme-color, apple) | ✅ vorhanden | ❌ fehlt |
| `/sw.js` Route | ❌ fehlt | ❌ fehlt |
| SW-Registrierung im HTML | ❌ fehlt | ❌ fehlt |

---

## Was hinzukommt

### Service Worker (`/sw.js`) — beide Apps identisch

Minimaler SW — nur für Installierbarkeit, kein Offline-Cache (App braucht Backend):

```javascript
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', e => e.respondWith(fetch(e.request)));
```

Flask-Route (in beiden Files):
```python
@app.route('/sw.js')
def sw_js():
    js = (
        "self.addEventListener('install', () => self.skipWaiting());\n"
        "self.addEventListener('activate', e => e.waitUntil(clients.claim()));\n"
        "self.addEventListener('fetch', e => e.respondWith(fetch(e.request)));\n"
    )
    return Response(js, mimetype='application/javascript')
```

### SW-Registrierung im HTML `<head>` — beide Apps

```html
<script>if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js');</script>
```

---

### Freund-App: Fehlende Routen + Meta-Tags

**`/manifest.json`:**
```python
@app.route('/manifest.json')
def manifest():
    return jsonify(
        name="BMO",
        short_name="BMO",
        start_url="/",
        display="standalone",
        background_color="#0f172a",
        theme_color="#5eead4",
        icons=[{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}]
    )
```

**`/icon.svg`:** Dieselbe `BMO_SVG`-Konstante aus `bmo_web.py` in `bmo_web_freund.py` kopieren + Route hinzufügen.

**HTML meta-tags** im `<head>` der Freund-App:
```html
<meta name="theme-color" content="#5eead4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="BMO">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon.svg">
<link rel="manifest" href="/manifest.json">
```

---

## Dateien

| Datei | Änderung |
|---|---|
| `D:\python\scripts\Bmo_main\src\bmo_web.py` | `/sw.js` Route + SW-Registrierungs-Script im HTML |
| `D:\python\scripts\Bmo_f_tmp2\bmo_web_freund.py` | `BMO_SVG` Konstante, `/icon.svg`, `/manifest.json`, `/sw.js` Routen + HTML meta-tags + SW-Script |

---

## Nicht im Scope

- Offline-Caching
- Push-Notifications
- Option C (kombinierte App) — separates Projekt
