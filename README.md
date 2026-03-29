# BMO – Freundes-Version 👾

**Du bist der Freund — dein Freund betreibt BMO auf seinem PC, und du kannst ihn darüber steuern.**

Das Denken (KI, Stimme) läuft auf dem PC deines Freundes. Spotify, Shutdown und alles andere läuft auf **deinem** PC.

---

## ✨ Was du damit kannst

| Feature | Beschreibung |
|---|---|
| 💬 Chat | Mit BMO schreiben oder sprechen |
| 🎤 Mikrofon | Spracheingabe direkt im Browser |
| 🎵 Spotify | Musik abspielen, pausieren, überspringen, Lautstärke |
| 💻 System-Stats | CPU, RAM, Uhrzeit anzeigen |
| ⏻ Shutdown | Deinen PC herunterfahren |
| 🔒 Admin-Zugriff | Deinem Freund erlauben, Jumpscare auszulösen oder deinen Bildschirm zu sehen |

---

## 🚀 Installation

### Schritt 1 · Voraussetzungen

| Was | Wo |
|---|---|
| Python 3.10 | https://python.org |
| Tailscale | https://tailscale.com *(um den Core deines Freundes zu erreichen)* |
| Git | https://git-scm.com *(optional, fürs Klonen)* |

> 💡 **Tailscale:** Kostenlos. Dein Freund schickt dir eine Einladung oder ihr teilt einen Account. Damit könnt ihr euch gegenseitig erreichen — egal wo ihr seid.

### Schritt 2 · Repo klonen

```bash
git clone https://github.com/HolziDape/Bmo_f.git
cd Bmo_f
```

Oder als ZIP herunterladen: **Code → Download ZIP**

### Schritt 3 · Abhängigkeiten installieren

Einfach `SETUP_EINMALIG.bat` doppelklicken — das installiert alles automatisch.

Oder manuell:
```bash
pip install flask flask-cors requests psutil spotipy pillow
```

> 💡 `spotipy` und `pillow` sind optional — ohne Spotify-Steuerung und Bildschirm-Streaming läuft alles andere trotzdem.

### Schritt 4 · config.txt ausfüllen

Öffne `config.txt` und trage die Tailscale-IP deines Freundes ein:

```
CORE_IP   = 100.x.x.x    ← Tailscale-IP deines Freundes (er findet sie mit: tailscale ip -4)
CORE_PORT = 6000
```

**Spotify** *(optional — nur wenn du Spotify-Steuerung willst)*:
```
SPOTIFY_CLIENT_ID     = HIER_CLIENT_ID_EINTRAGEN
SPOTIFY_CLIENT_SECRET = HIER_CLIENT_SECRET_EINTRAGEN
SPOTIFY_REDIRECT_URI  = http://127.0.0.1:8888/callback
SPOTIFY_PLAYLIST_ID   = HIER_PLAYLIST_ID_EINTRAGEN
```

> Spotify-App anlegen: [developer.spotify.com](https://developer.spotify.com/dashboard) → App erstellen → Redirect URI `http://127.0.0.1:8888/callback` eintragen → Client ID + Secret kopieren.

### Schritt 5 · Starten

```
START_WEB.bat  ← Doppelklick
```

Beim **ersten Start** öffnet sich automatisch `http://localhost:5000/setup` — dort ein Passwort wählen, fertig.

Ab dann öffnet sich der Browser direkt mit dem Login.

---

## 🔒 Admin-Zugriff (Jumpscare & Screen)

Dein Freund kann optional folgendes bei dir auslösen — **aber nur wenn du es erlaubst**:

| Funktion | Was passiert |
|---|---|
| 👻 Jumpscare | Schreck-Overlay auf deinem Bildschirm mit Ton |
| 🖥️ Screen live | Dein Freund sieht deinen Bildschirm in Echtzeit |

**So aktivierst du es:**
1. BMO öffnen → auf den `🔒 Admin`-Button klicken
2. „Admin-Zugriff aktivieren" → ab jetzt kann dein Freund die Funktionen nutzen
3. Jederzeit wieder deaktivieren — einfach nochmal klicken

---

## ❓ Häufige Probleme

**„Core nicht erreichbar"**
→ Dein Freund muss BMO gestartet haben. Tailscale prüfen — beide müssen online sein.

**Browser öffnet sich nicht automatisch**
→ Manuell aufrufen: `http://localhost:5000`

**Spotify funktioniert nicht**
→ `config.txt` prüfen — Client ID und Secret korrekt eingetragen?
→ Beim ersten Mal öffnet sich ein Browser-Fenster zur Spotify-Anmeldung — das ist normal.

**Bildschirm-Streaming geht nicht**
→ `pip install pillow` ausführen.

---

## 🔗 Links

- [Admin-Version (Haupt-Repo)](https://github.com/HolziDape/Bmo-fr)
- [Tailscale](https://tailscale.com)

---

## 📄 Lizenz

MIT — Fan-Projekt, nicht offiziell mit Cartoon Network / Adventure Time verbunden.
