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
_PONG_HTML = r"""<!DOCTYPE html>
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
<div id="info">Gewinne 10 Runden &rarr; +{{ points }} &#11088;</div>
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
  ctx.setLineDash([8,8]);ctx.strokeStyle='#1e293b';ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle='#334155';ctx.font='bold 32px sans-serif';ctx.textAlign='center';
  ctx.fillText(wins,W/4,40);ctx.fillText(losses,3*W/4,40);
  ctx.fillStyle='#64748b';ctx.font='12px sans-serif';
  ctx.fillText('Wins',W/4,58);ctx.fillText('Verloren',3*W/4,58);
  ctx.fillStyle='#22c55e';ctx.beginPath();
  ctx.roundRect(4,py,PW,PH,4);ctx.fill();
  ctx.fillStyle='#ef4444';ctx.beginPath();
  ctx.roundRect(W-PW-4,ay,PW,PH,4);ctx.fill();
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(bx,by,BALL,0,Math.PI*2);ctx.fill();
}

function loop(){
  if(!running)return;
  const aim=by-(PH/2);
  ay+=(aim-ay)*0.1;
  ay=Math.max(0,Math.min(H-PH,ay));
  bx+=vx;by+=vy;
  if(by-BALL<0){by=BALL;vy*=-1;}
  if(by+BALL>H){by=H-BALL;vy*=-1;}
  if(bx-BALL<PW+4&&by>py&&by<py+PH){bx=PW+4+BALL;vx=Math.abs(vx)*(1+0.05*wins);vy+=(by-(py+PH/2))*0.1;}
  if(bx+BALL>W-PW-4&&by>ay&&by<ay+PH){bx=W-PW-4-BALL;vx=-Math.abs(vx)*(1+0.05*wins);}
  if(bx<0){losses++;document.getElementById('msg').textContent='Verloren! '+wins+'/10 Wins';resetBall(1);}
  if(bx>W){wins++;document.getElementById('msg').textContent=wins<10?'Gewonnen! '+wins+'/10 Wins':' ';resetBall(-1);}
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
  document.getElementById('msg').textContent='+'+d.earned+' \u2B50 \u2192 jetzt '+d.points+' Punkte! Fenster schlie\xDFen.';
}

resetBall();loop();
</script>
</body>
</html>"""

_GAME_PAGES: dict = {
    'pong':     _PONG_HTML,
    'tetris':   '',
    'snake':    '',
    'breakout': '',
}
