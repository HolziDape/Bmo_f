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
