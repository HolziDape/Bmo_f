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

def _cleanup_sessions():
    """Entfernt Sessions die älter als 2 Stunden sind."""
    cutoff = time.time() - 7200
    with _sessions_lock:
        expired = [t for t, s in _sessions.items() if s['start'] < cutoff]
        for t in expired:
            del _sessions[t]


@games_bp.route('/games/<game>')
def game_page(game):
    if game not in MIN_GAME_SECONDS:
        return 'Spiel nicht gefunden', 404
    token = secrets.token_hex(16)
    with _sessions_lock:
        _sessions[token] = {'game': game, 'start': time.time()}
    _cleanup_sessions()
    return render_template_string(_GAME_PAGES[game], token=token, points=GAME_POINTS[game])


@games_bp.route('/api/games/complete', methods=['POST'])
def api_games_complete():
    """Verifiziert Spiel-Ergebnis und gibt neue Punkte zurück."""
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


# Game HTML pages — filled in Tasks 6-9
_GAME_PAGES: dict = {
    'pong':     '',
    'tetris':   '',
    'snake':    '',
    'breakout': '',
}
