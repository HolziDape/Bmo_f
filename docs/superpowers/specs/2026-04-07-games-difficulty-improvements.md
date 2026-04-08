# Games: Difficulty Levels, Tetris Improvements & Multiplayer Button — Design Spec
**Datum:** 2026-04-07  
**Projekt:** BMO-F (bmo_games.py + bmo_web_freund.py)  
**Status:** Genehmigt

---

## Überblick

Vier Verbesserungen an den BMO Mini-Spielen:
1. Schwierigkeitsgrade (Easy/Normal/Hard/Insane) mit Punkte-Multiplikatoren und angepassten Spielparametern
2. Tetris: Ghost Piece + Hard Drop (Leertaste + Mobile-Button)
3. Pong Mindestzeit-Bug behoben (60s → 30s)
4. Pong-Button → Multiplayer-Button mit eigenem Overlay

---

## 1. Schwierigkeitsgrade

### Auswahl-UI
- Im Spiele-Overlay erscheinen unter jedem Spiel 4 Difficulty-Buttons: Easy / Normal / Hard / Insane
- Klick öffnet das Spiel mit URL-Parameter: `/games/pong?diff=hard`
- `game_page()` in `bmo_games.py` liest `request.args.get('diff', 'normal')` und übergibt den Wert als Template-Variable

### Punkte-Multiplikatoren

| Difficulty | Multiplikator | Pong | Tetris | Snake | Breakout |
|---|---|---|---|---|---|
| easy | ×0.5 | 15 | 12 | 10 | 7 |
| normal | ×1 | 30 | 25 | 20 | 15 |
| hard | ×1.5 | 45 | 37 | 30 | 22 |
| insane | ×2 | 60 | 50 | 40 | 30 |

Berechnung: `math.floor(BASE_POINTS[game] * MULTIPLIER[diff])`

### Spielparameter

**Pong:**
| Difficulty | Ballgeschwindigkeit (SPEED) | KI-Reaktion (Faktor) |
|---|---|---|
| easy | 3 | 0.06 |
| normal | 4 | 0.10 |
| hard | 5.5 | 0.14 |
| insane | 7 | 0.19 |

**Tetris:** Nur Punkte-Multiplikator (Fallgeschwindigkeit wächst bereits durch Level)

**Snake:**
| Difficulty | Tick-Intervall |
|---|---|
| easy | 200ms |
| normal | 150ms |
| hard | 100ms |
| insane | 65ms |

**Breakout:**
| Difficulty | Ballgeschwindigkeit (vx/vy) |
|---|---|
| easy | 2.5 / 3.5 |
| normal | 3 / 4 |
| hard | 4.5 / 5.5 |
| insane | 6 / 7 |

### Backend-Änderungen (`bmo_games.py`)
- `GAME_POINTS` wird zu `BASE_POINTS` (unverändertes Dict)
- Neues Dict `DIFF_MULTIPLIER = {'easy': 0.5, 'normal': 1.0, 'hard': 1.5, 'insane': 2.0}`
- `game_page()` liest `diff` aus Query-Parameter, übergibt es als Template-Variable
- `_sessions` speichert zusätzlich `{'game': ..., 'start': ..., 'diff': ..., 'earned': ...}`
- `api_games_complete()` liest `earned` aus Session statt aus `GAME_POINTS`

---

## 2. Tetris-Verbesserungen

### Ghost Piece
- Berechnet die tiefste Y-Position wo `cur` noch passt (`fits(cur.s, cx, ghostY)`)
- Wird in `draw()` vor dem echten Piece gezeichnet: gleiche Farbe mit `globalAlpha = 0.25`
- Nur sichtbar wenn Ghost-Y ≠ aktuelle Y (sonst überlappt es sich)

### Hard Drop
- **Keyboard:** Leertaste → `while fits(cur.s, cx, cy+1): cy++; place()`
- **Mobile:** Zusätzlicher "⬇⬇" Button in `.ctrl` div
- Leertaste-Event in `document.addEventListener('keydown')` ergänzen

---

## 3. Pong Bug-Fix

- `MIN_GAME_SECONDS['pong']` von 60 auf **30** reduzieren
- Difficulty-abhängige Mindestzeiten:

| Difficulty | pong | tetris | snake | breakout |
|---|---|---|---|---|
| easy | 20 | 30 | 20 | 15 |
| normal | 30 | 60 | 30 | 20 |
| hard | 30 | 60 | 30 | 20 |
| insane | 30 | 60 | 30 | 20 |

(Easy hat kürzere Mindestzeiten weil es schneller geht)

---

## 4. Multiplayer-Button

### Änderungen in `bmo_web_freund.py`
- Bestehender Pong-Button (`onclick="showPong()"`) wird umbenannt zu **"Multi 🎮"**
- `onclick` öffnet neues `multiplayerOverlay` statt direkt `pongOverlay`
- Neues `multiplayerOverlay`: Sheet mit Titel "Multiplayer" und einem Eintrag:
  - **"🏓 Pong mit Admin"** → öffnet den bestehenden `pongOverlay`
- `pongBadge` bleibt am Multiplayer-Button (zeigt weiterhin `!` wenn Admin wartet)

---

## Betroffene Dateien

| Datei | Änderungen |
|---|---|
| `bmo_games.py` | Difficulty-Parameter, BASE_POINTS, DIFF_MULTIPLIER, Session speichert earned, Ghost Piece + Hard Drop in Tetris-HTML, Difficulty-URLs in Pong/Snake/Breakout-HTML |
| `bmo_web_freund.py` | Spiele-Overlay bekommt Difficulty-Buttons, Multiplayer-Overlay, Button-Umbenennung |
