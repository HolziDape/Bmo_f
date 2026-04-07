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

# ── Difficulty-System Tests ──────────────────────────────────────
import math as _math
from bmo_games import BASE_POINTS, DIFF_MULTIPLIER

def test_diff_multiplier_easy():
    result = _math.floor(BASE_POINTS['pong'] * DIFF_MULTIPLIER['easy'])
    assert result == 15

def test_diff_multiplier_insane():
    result = _math.floor(BASE_POINTS['tetris'] * DIFF_MULTIPLIER['insane'])
    assert result == 50

def test_diff_multiplier_hard_snake():
    result = _math.floor(BASE_POINTS['snake'] * DIFF_MULTIPLIER['hard'])
    assert result == 30
