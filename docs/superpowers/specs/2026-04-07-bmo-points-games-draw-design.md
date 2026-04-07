# BMO Points, Games, Draw & Lite-Mode — Design Spec
**Datum:** 2026-04-07  
**Projekt:** BMO-F (Freund) + BMO-Main (Admin)  
**Status:** Genehmigt

---

## Überblick

Der Freund kann Mini-Spiele spielen, dabei Punkte sammeln und diese Punkte ausgeben um Features beim Admin auszulösen (Jumpscare, Screen-Draw, etc.). Punkte werden lokal im Browser gespeichert, HMAC-signiert (Manipulationsschutz) und beim nächsten Connect mit dem Admin synchronisiert. Zusätzlich bekommt der Admin einen Lite-Mode Toggle, der Ollama/TTS beim Start überspringt.

---

## Architektur

### Neue Dateien (Freund-PC — `Bmo_f_tmp2/`)

**`bmo_points.py`** — Python-Modul (kein eigener Server)  
- Wird von `bmo_web_freund.py` importiert  
- Verwaltet: HMAC-Signierung, Punkte-Validierung, Sync-Logik, Feature-Kosten-Config  
- Speicherort Admin: `_intern/data/points_<freund_id>.json` (Freund-ID = Tailscale-IP, aus `config.txt`)

**`bmo_games.py`** — Flask-Blueprint  
- Registriert in `bmo_web_freund.py`  
- Enthält Routes + Inline-Canvas-JS für alle Spiele  
- Einheitliches Interface: `GameManager.complete(game, score)` → Punkte an `bmo_points`

### Änderungen bestehender Dateien

| Datei | Änderung |
|---|---|
| `bmo_web_freund.py` | importiert bmo_points + bmo_games, Punkte-Anzeige in UI, Draw-Overlay |
| `bmo_core.py` (Admin) | Lite-Mode Toggle, Draw-Empfang-Endpunkt, Punkte-Sync Endpunkt |

---

## Punkte-System & Sicherheit

### HMAC-Signierung
- Shared Secret in `config.txt`: `POINTS_SECRET=<auto-generiert beim ersten Start>`
- Signatur: `hmac(secret, f"{points}:{timestamp}")`
- Beim Sync: Admin verifiziert Signatur — bei Fehler wird auf letzten bekannten validen Stand zurückgesetzt

### Punkte verdienen

| Spiel | Bedingung | Punkte |
|---|---|---|
| Pong (solo) | 10 Runden gewinnen | 30 |
| Tetris | Level 5 erreichen | 25 |
| Snake | 20 Äpfel essen | 20 |
| Breakout | Stage abschließen | 15 |

### Punkte ausgeben (anpassbare Defaults)

| Feature | Standard-Kosten |
|---|---|
| Jumpscare beim Admin | 50 |
| Admin-Screen ansehen | 30 |
| Auf Admin-Screen malen | 40 |
| Admin malt auf Freund-Screen | kostenlos (Admin-initiiert) |

Admin kann Standardkosten im Web-Interface überschreiben → gespeichert in `bmo_config.txt`.

### Sync-Logik
- Beim Öffnen der Web-App: lokaler Stand → POST `/api/points/sync`
- Admin antwortet mit verifiziertem Stand
- Offline gespielt: Punkte in `localStorage` mit Signatur, Sync beim nächsten Connect

---

## Spiele

### Pong — Solo-Modus (bestehenden Code erweitern)
- Aktueller Multiplayer-Pong bleibt erhalten
- Neuer Solo-Modus: Freund vs. KI-Gegner
- Im Pong-Overlay: Buttons "Solo spielen" | "Mit Admin spielen"
- Ziel: 10 Runden gewinnen → 30 Punkte

### Tetris, Snake, Breakout
- Alle als Inline-Canvas-JS in `bmo_games.py` (Flask Blueprint)
- Jedes Spiel als eigenes Overlay (wie bestehender Pong-Overlay)
- Neue Buttons in der Schnellzugriff-Leiste der Web-UI

### Anti-Cheat
- Punkte werden erst nach Server-Bestätigung gutgeschrieben (`POST /api/games/complete`)
- Server prüft: war eine aktive Spiel-Session offen?
- Plausibilitätscheck: z.B. kein Tetris Level 5 in unter 30 Sekunden
- Session-Token pro Spiel-Start verhindert doppeltes Einreichen desselben Ergebnisses

---

## Draw-Feature

### Freund malt auf Admin-Screen
1. Freund hat genug Punkte → klickt "Admin-Screen bemalen"
2. Punkte werden abgezogen, Server öffnet tkinter-Canvas-Overlay auf Admin-Monitor (wie Jumpscare)
3. Freund zeichnet im Browser-Canvas → Striche als JSON an `POST /api/draw/stroke`
4. Admin-Overlay pollt `/api/draw/strokes` alle 200ms → rendert Striche in Echtzeit
5. Schließen via Admin-Button oder Timeout nach 60 Sekunden

### Admin malt auf Freund-Screen
1. Admin klickt "Auf Freund-Screen malen" im Admin-Web
2. Admin zeichnet im Browser-Canvas → Striche an `POST /api/draw/friend-stroke`
3. Freund-Browser pollt → rendert Striche als transparentes Overlay über die gesamte UI
4. Freund kann mit "Schließen"-Button entfernen

---

## Lite-Mode

- **Toggle-Button** im Admin-Web-Interface (neben bestehenden Admin-Buttons)
- Speichert `LITE_MODE=true/false` in `bmo_config.txt`
- `bmo_core.py` beim Start: wenn `LITE_MODE=true` → Ollama nicht initialisiert, TTS nicht geladen, Wake-Word deaktiviert
- **Was im Lite-Mode läuft:** Web-Interface, Jumpscare, Draw-Overlay, Punkte-Sync, Screen-Share
- **Was deaktiviert ist:** KI (Ollama), Stimme (RVC/TTS), Wake-Word
- Umschalten im laufenden Betrieb → Neustart-Hinweis wird angezeigt

---

## Dateistruktur nach Implementierung

```
Bmo_f_tmp2/
├── bmo_web_freund.py      (erweitert: Points-UI, Draw-Overlay, Game-Buttons)
├── bmo_points.py          (neu: HMAC, Sync, Kosten-Config)
├── bmo_games.py           (neu: Blueprint, Pong-Solo, Tetris, Snake, Breakout)
└── config.txt             (+ POINTS_SECRET, LITE_MODE, Feature-Kosten)

Bmo_main/src/
└── bmo_core.py            (erweitert: Lite-Mode, Draw-Endpunkt, Punkte-Sync)
```
