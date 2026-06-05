from flask import Blueprint, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.data.tournament import GROUPS, TEAMS, team_name
from app.services.scoring import build_standings
from app.storage import get_storage


public_bp = Blueprint("public", __name__)

# ---------------------------------------------------------------------------
# Shared CSS / header used by all pages
# ---------------------------------------------------------------------------
_BASE_STYLE = """
<style>
  :root{--ink:#10251d;--muted:#60756d;--line:#d9e6df;--wash:#eef7f2;--paper:#fff;
    --pitch:#138455;--pitch-dark:#073f2b;--pitch-deep:#052d21;--gold:#d8b24a;--blue:#215f9f;}
  *{box-sizing:border-box;}
  body{margin:0;min-height:100vh;padding-top:96px;color:var(--ink);
    font-family:Poppins,Inter,system-ui,-apple-system,"Segoe UI",sans-serif;
    background:linear-gradient(90deg,rgba(7,63,43,.05) 1px,transparent 1px),
      linear-gradient(180deg,rgba(7,63,43,.05) 1px,transparent 1px),
      linear-gradient(180deg,#f8fbf9 0%,var(--wash) 58%,#e7f2ec 100%);
    background-size:64px 64px,64px 64px,auto;}
  .topbar{position:fixed;top:0;left:0;right:0;z-index:20;display:grid;
    grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;
    padding:14px clamp(14px,4vw,48px);color:#fff;
    background:linear-gradient(120deg,rgba(255,255,255,.08),transparent 34%),
      linear-gradient(135deg,var(--pitch-deep),var(--pitch));
    border-radius:0 0 36px 36px;box-shadow:0 14px 32px rgba(7,63,43,.22);}
  .brand{display:flex;align-items:center;justify-content:center;gap:10px;
    font-weight:850;text-decoration:none;color:inherit;text-align:center;}
  .mark{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.34);color:#fff;}
  .brand small{display:block;color:rgba(255,255,255,.78);font-weight:700;font-size:.78rem;}
  .nav{display:flex;gap:8px;flex-wrap:wrap;}
  .nav:last-child{justify-content:flex-end;}
  .nav a,.btn{border:0;border-radius:8px;padding:10px 18px;background:#fff;
    color:var(--pitch-dark);font-weight:850;text-decoration:none;
    box-shadow:0 6px 14px rgba(5,45,33,.14);cursor:pointer;font:inherit;font-size:.92rem;}
  .btn-primary{background:var(--pitch);color:#fff;}
  .btn-primary:hover{background:var(--pitch-dark);}
  .shell{width:min(1200px,calc(100% - 32px));margin:0 auto;padding:28px 0 64px;}
  .card{overflow:hidden;border:1px solid rgba(16,37,29,.08);border-radius:10px;
    background:var(--paper);box-shadow:0 20px 56px rgba(7,63,43,.12);}
  .section-header{padding:26px 30px;color:#fff;
    background:linear-gradient(135deg,var(--pitch-deep),var(--pitch));}
  .section-header h1,.section-header h2{margin:0;line-height:1;}
  .eyebrow{margin:0 0 8px;font-size:.76rem;font-weight:900;letter-spacing:.12em;
    text-transform:uppercase;opacity:.75;}
  .body-pad{padding:24px 30px;}
  .error{color:#a33a2a;font-weight:750;margin:0;}
  .hint{color:var(--muted);font-size:.9rem;margin:0;}
  label{color:var(--muted);font-weight:850;font-size:.9rem;}
  input,select{width:100%;min-height:46px;padding:10px 12px;
    border:1px solid var(--line);border-radius:8px;color:var(--ink);
    font:inherit;background:#fbfdfc;}
  input:focus,select:focus{outline:3px solid rgba(15,107,79,.16);border-color:var(--pitch);}
  @media(max-width:760px){
    body{padding-top:112px;}
    .topbar{grid-template-columns:1fr;}
    .brand{order:-1;}
    .nav,.nav:last-child{justify-content:center;}
  }
</style>
"""

def _topbar(show_logout=False):
    extra = '<a href="' + url_for('public.logout') + '">Salir</a>' if show_logout else ''
    return f"""
<header class="topbar">
  <nav class="nav"><a href="{url_for('public.welcome')}">Inicio</a></nav>
  <a class="brand" href="{url_for('public.welcome')}">
    <span class="mark">26</span>
    <span>PORRA MUNDIAL 2026<small>Elecnor Sistemas</small></span>
  </a>
  <nav class="nav"><a href="{url_for('public.ranking')}">Clasificación</a>{extra}</nav>
</header>"""


# ---------------------------------------------------------------------------
# WELCOME / AUTH
# ---------------------------------------------------------------------------
WELCOME_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Porra Mundial 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;850;900&display=swap" rel="stylesheet">
""" + _BASE_STYLE + """
<style>
  .hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,420px);
    gap:32px;align-items:stretch;padding:clamp(24px,5vw,52px);
    background:linear-gradient(90deg,rgba(19,132,85,.07) 1px,transparent 1px),
      linear-gradient(180deg,#fff 0%,#f6fbf8 100%);
    background-size:42px 42px,auto;border-bottom:1px solid var(--line);}
  .copy{display:flex;flex-direction:column;justify-content:center;min-height:300px;}
  h1{margin:0 0 14px;color:var(--pitch-dark);font-size:clamp(2.4rem,5vw,4.8rem);line-height:.96;}
  .lead{max-width:640px;margin:0;color:var(--muted);font-size:1.08rem;line-height:1.56;}
  .flagline{display:flex;flex-wrap:wrap;gap:7px;margin:20px 0 0;}
  .flagline img{width:32px;height:22px;object-fit:cover;border-radius:3px;
    box-shadow:0 1px 4px rgba(16,37,29,.18);}
  .pitch-card{position:relative;min-height:300px;padding:20px;color:#fff;border-radius:8px;
    overflow:hidden;
    background:linear-gradient(90deg,rgba(255,255,255,.10) 1px,transparent 1px),
      linear-gradient(180deg,rgba(255,255,255,.08) 1px,transparent 1px),
      linear-gradient(135deg,#075136 0%,#138455 58%,#215f9f 100%);
    background-size:44px 44px,44px 44px,auto;
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.18),0 20px 40px rgba(7,63,43,.2);}
  .pitch-card::before{content:"";position:absolute;inset:24px;
    border:2px solid rgba(255,255,255,.32);border-radius:8px;}
  .pitch-card::after{content:"";position:absolute;left:50%;top:50%;width:110px;height:110px;
    transform:translate(-50%,-50%);border:2px solid rgba(255,255,255,.32);border-radius:50%;}
  .scoreboard{position:relative;z-index:1;display:grid;gap:12px;}
  .score-top{display:flex;justify-content:space-between;align-items:center;gap:10px;}
  .score-top span{padding:6px 9px;border-radius:7px;background:rgba(255,255,255,.14);
    font-size:.75rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;}
  .match{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;
    margin-top:22px;padding:12px;border-radius:8px;
    background:rgba(5,45,33,.58);backdrop-filter:blur(4px);}
  .team{display:grid;gap:5px;justify-items:center;font-weight:900;}
  .team img{width:40px;height:27px;object-fit:cover;border-radius:3px;}
  .versus{color:var(--gold);font-weight:950;}
  .groups{position:absolute;z-index:1;left:20px;right:20px;bottom:20px;
    display:grid;grid-template-columns:repeat(3,1fr);gap:7px;}
  .group-chip{min-height:66px;padding:9px;border-radius:7px;
    background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.16);}
  .group-chip strong{display:block;margin-bottom:5px;color:#fff3c4;font-size:.79rem;}
  .group-chip span{display:block;color:rgba(255,255,255,.8);font-size:.74rem;line-height:1.3;}
  .auth{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));background:#fff;}
  form.auth-form{display:grid;gap:12px;padding:28px;border-right:1px solid var(--line);}
  form.auth-form.accent{border-right:0;box-shadow:inset 5px 0 0 var(--pitch);}
  @media(max-width:860px){
    .hero{grid-template-columns:1fr;}
    .copy{min-height:auto;}
    .auth{grid-template-columns:1fr;}
    form.auth-form,form.auth-form.accent{border-right:0;border-top:1px solid var(--line);}
    .groups{grid-template-columns:1fr;position:relative;left:auto;right:auto;bottom:auto;margin-top:16px;}
    .pitch-card{min-height:auto;}
  }
</style>
</head><body>
{{ topbar | safe }}
<main class="shell">
  <section class="card">
    <div class="hero">
      <div class="copy">
        <p class="eyebrow" style="color:var(--pitch)">Elecnor Sistemas</p>
        <h1>La porra del Mundial empieza aquí</h1>
        <p class="lead">Regístrate, entra al marcador y compite con tus compañeros durante todo el torneo.</p>
        <div class="flagline" aria-hidden="true">
          <img src="https://flagcdn.com/w40/es.png" alt=""><img src="https://flagcdn.com/w40/ar.png" alt="">
          <img src="https://flagcdn.com/w40/br.png" alt=""><img src="https://flagcdn.com/w40/fr.png" alt="">
          <img src="https://flagcdn.com/w40/de.png" alt=""><img src="https://flagcdn.com/w40/us.png" alt="">
          <img src="https://flagcdn.com/w40/mx.png" alt=""><img src="https://flagcdn.com/w40/ca.png" alt="">
        </div>
      </div>
      <aside class="pitch-card">
        <div class="scoreboard">
          <div class="score-top"><span>Mundial 2026</span><span>Porra interna</span></div>
          <div class="match">
            <div class="team"><img src="https://flagcdn.com/w80/es.png" alt="España"><span>ESP</span></div>
            <div class="versus">VS</div>
            <div class="team"><img src="https://flagcdn.com/w80/br.png" alt="Brasil"><span>BRA</span></div>
          </div>
        </div>
        <div class="groups" aria-hidden="true">
          <div class="group-chip"><strong>Fase de grupos</strong><span>Pronósticos por partido</span></div>
          <div class="group-chip"><strong>Ranking vivo</strong><span>Puntos y posiciones</span></div>
          <div class="group-chip"><strong>Final</strong><span>Todos contra todos</span></div>
        </div>
      </aside>
    </div>
    <div class="auth">
      <form class="auth-form" method="post" action="{{ url_for('public.login') }}">
        <div><p class="eyebrow">Acceso</p><h2 style="margin:0;color:var(--pitch-dark)">Ya participo</h2></div>
        <label for="login-email">Email</label>
        <input id="login-email" name="email" type="email" autocomplete="email" required>
        <label for="login-password">PIN o contraseña</label>
        <input id="login-password" name="password" type="password" autocomplete="current-password" required>
        {% if login_error %}<p class="error">{{ login_error }}</p>{% endif %}
        <button class="btn btn-primary" type="submit">Entrar</button>
      </form>
      <form class="auth-form accent" method="post" action="{{ url_for('public.register') }}">
        <div><p class="eyebrow">Registro</p><h2 style="margin:0;color:var(--pitch-dark)">Nuevo participante</h2></div>
        <label for="reg-name">Nombre</label>
        <input id="reg-name" name="name" type="text" autocomplete="name" value="{{ suggested_name or '' }}" required>
        <label for="reg-email">Email</label>
        <input id="reg-email" name="email" type="email" autocomplete="email" required>
        <label for="reg-password">PIN (mínimo 4 caracteres)</label>
        <input id="reg-password" name="password" type="password" minlength="4" autocomplete="new-password" required>
        {% if register_error %}<p class="error">{{ register_error }}</p>{% endif %}
        <button class="btn btn-primary" type="submit">Registrarme</button>
      </form>
    </div>
  </section>
</main></body></html>
"""

# ---------------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------------
RANKING_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clasificación – Porra Mundial 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;850;900&display=swap" rel="stylesheet">
""" + _BASE_STYLE + """
<style>
  :root{--silver:#c6d0ca;--bronze:#c97d4d;}
  ol{display:grid;gap:9px;padding:0;margin:0;list-style:none;}
  li{display:grid;grid-template-columns:48px minmax(0,1fr) auto auto;
    gap:12px;align-items:center;min-height:64px;padding:10px 14px;
    border:1px solid var(--line);border-radius:8px;background:#fbfdfc;}
  li:nth-child(1){border-color:rgba(216,178,74,.55);background:linear-gradient(90deg,rgba(216,178,74,.12),#fff);}
  li:nth-child(2){border-color:rgba(198,208,202,.75);}
  li:nth-child(3){border-color:rgba(201,125,77,.45);}
  .rank{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;
    background:#e8f2ed;color:var(--pitch);font-weight:950;}
  li:nth-child(1) .rank{background:var(--gold);color:#2d2206;}
  li:nth-child(2) .rank{background:var(--silver);color:#23342c;}
  li:nth-child(3) .rank{background:var(--bronze);color:#fff;}
  .name strong{display:block;color:var(--pitch-dark);font-size:1rem;}
  .name span{color:var(--muted);font-size:.85rem;}
  .points{padding:7px 10px;border-radius:7px;background:#eef7f2;
    color:var(--pitch-dark);font-weight:950;white-space:nowrap;}
  .view-link{font-size:.82rem;color:var(--pitch);text-decoration:none;font-weight:750;white-space:nowrap;}
  .empty{padding:36px 20px;border:1px dashed var(--line);border-radius:8px;
    color:var(--muted);font-weight:750;text-align:center;}
  .summary{display:grid;grid-template-columns:repeat(2,minmax(100px,1fr));gap:9px;min-width:230px;}
  .stat{padding:12px;border-radius:8px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.18);}
  .stat strong{display:block;font-size:1.5rem;}
  .stat span{color:rgba(255,255,255,.78);font-size:.78rem;font-weight:800;text-transform:uppercase;}
  .rh{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;
    align-items:end;padding:28px 30px;color:#fff;
    background:linear-gradient(90deg,rgba(255,255,255,.10) 1px,transparent 1px),
      linear-gradient(180deg,rgba(255,255,255,.08) 1px,transparent 1px),
      linear-gradient(135deg,#073f2b 0%,#138455 68%,#215f9f 100%);
    background-size:46px 46px,46px 46px,auto;}
  .cta-bar{padding:18px 30px;background:#f3faf6;border-top:1px solid var(--line);
    display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
  @media(max-width:720px){
    li{grid-template-columns:38px minmax(0,1fr) auto;}
    .view-link{display:none;}
    .rh{grid-template-columns:1fr;}
    .summary{min-width:0;}
  }
</style>
</head><body>
{{ topbar | safe }}
<main class="shell">
  <section class="card">
    <div class="rh">
      <div><p class="eyebrow">Clasificación</p><h1>Ranking general</h1></div>
      <div class="summary">
        <div class="stat"><strong>{{ standings|length }}</strong><span>Participantes</span></div>
        <div class="stat"><strong>2026</strong><span>Mundial</span></div>
      </div>
    </div>
    {% if current_user and not has_prediction %}
    <div class="cta-bar">
      <span style="color:var(--muted);font-weight:750;">Aún no has hecho tu predicción.</span>
      <a class="btn btn-primary" href="{{ url_for('public.grupos_fase') }}">Hacer mi predicción →</a>
    </div>
    {% elif current_user %}
    <div class="cta-bar">
      <a class="btn" href="{{ url_for('public.grupos_fase') }}" style="font-size:.88rem;">Editar predicción</a>
      <a class="btn" href="{{ url_for('public.ver_prediccion', participant_id=session.get('participant_id')) }}" style="font-size:.88rem;">Ver mi predicción</a>
    </div>
    {% endif %}
    <div class="body-pad">
      {% if standings %}
      <ol>
        {% for row in standings %}
        <li>
          <span class="rank">{{ loop.index }}</span>
          <span class="name"><strong>{{ row.name }}</strong><span>Participante Elecnor</span></span>
          <span class="points">{{ row.points }} pts</span>
          <a class="view-link" href="{{ url_for('public.ver_prediccion', participant_id=row.id) }}">Ver predicción</a>
        </li>
        {% endfor %}
      </ol>
      {% else %}
      <div class="empty">Todavía no hay participantes. ¡Sé el primero en registrarte!</div>
      {% endif %}
    </div>
  </section>
</main></body></html>
"""

# ---------------------------------------------------------------------------
# GRUPOS PREDICTION FORM
# ---------------------------------------------------------------------------
GRUPOS_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fase de Grupos – Porra Mundial 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;850;900&display=swap" rel="stylesheet">
""" + _BASE_STYLE + """
<style>
  .info-card{background:#f0faf5;border:1px solid #b2dcc6;border-radius:9px;padding:18px 22px;margin-bottom:22px;}
  .info-card p{margin:4px 0;color:var(--muted);font-size:.92rem;}
  .groups-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;}
  .group-card{border:1px solid var(--line);border-radius:9px;overflow:hidden;}
  .group-card-header{background:var(--pitch);color:#fff;padding:10px 14px;font-weight:850;font-size:1rem;}
  .group-card-body{background:#f8fbf9;padding:12px;}
  .team-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #e8f0eb;font-size:.88rem;font-weight:700;}
  .team-row:last-child{border-bottom:0;}
  .team-row img{width:22px;height:15px;object-fit:cover;border-radius:2px;}
  .selects{display:grid;gap:8px;margin-top:10px;}
  select{min-height:40px;font-size:.88rem;}
  .counter-bar{position:sticky;bottom:0;background:#fff;border-top:2px solid var(--line);
    padding:16px 20px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;justify-content:center;}
  .badge{display:inline-block;padding:6px 14px;border-radius:20px;font-weight:850;font-size:.88rem;}
  .badge-ok{background:#d4edda;color:#0f5132;}
  .badge-fail{background:#fde8e4;color:#8b2215;}
</style>
</head><body>
{{ topbar | safe }}
<main class="shell">
  <section class="card">
    <div class="section-header">
      <p class="eyebrow">Paso 1 de 2</p>
      <h2>Fase de Grupos</h2>
    </div>
    <div class="body-pad">
      <div class="info-card">
        <p><strong>Selecciona el 1º y 2º</strong> de cada grupo (obligatorio).</p>
        <p>Elige exactamente <strong>8 mejores terceros</strong> en total (los que pasan de la fase de grupos).</p>
      </div>
      <form method="post" id="form-grupos">
        <div class="groups-grid">
          {% for letra, team_ids in groups.items() %}
          <div class="group-card">
            <div class="group-card-header">Grupo {{ letra }}</div>
            <div class="group-card-body">
              {% for tid in team_ids %}
              {% set t = teams[tid] %}
              <div class="team-row">
                <img src="https://flagcdn.com/w40/{{ t.flag }}.png" alt="{{ t.name }}">
                {{ t.name }}
              </div>
              {% endfor %}
              <div class="selects">
                <select name="g_{{ letra }}_1" required class="grp-select" data-letra="{{ letra }}">
                  <option value="" disabled {{ '' if saved.get('g_' ~ letra ~ '_1') else 'selected' }}>1º clasificado…</option>
                  {% for tid in team_ids %}
                  <option value="{{ teams[tid].name }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_1') == teams[tid].name }}>{{ teams[tid].name }}</option>
                  {% endfor %}
                </select>
                <select name="g_{{ letra }}_2" required class="grp-select" data-letra="{{ letra }}">
                  <option value="" disabled {{ '' if saved.get('g_' ~ letra ~ '_2') else 'selected' }}>2º clasificado…</option>
                  {% for tid in team_ids %}
                  <option value="{{ teams[tid].name }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_2') == teams[tid].name }}>{{ teams[tid].name }}</option>
                  {% endfor %}
                </select>
                <select name="g_{{ letra }}_3" class="grp-select tercero" data-letra="{{ letra }}">
                  <option value="">3º · No pasa (eliminado)</option>
                  {% for tid in team_ids %}
                  <option value="{{ teams[tid].name }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_3') == teams[tid].name }}>{{ teams[tid].name }} · pasa como mejor 3º</option>
                  {% endfor %}
                </select>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
        <div class="counter-bar">
          <span id="badge-grupos" class="badge badge-fail">Grupos: 0/12</span>
          <span id="badge-terceros" class="badge badge-fail">Mejores terceros: 0/8</span>
          <button type="submit" id="btn-sig" class="btn btn-primary" disabled>Continuar a eliminatorias →</button>
        </div>
      </form>
    </div>
  </section>
</main>
<script>
function validate(){
  var letras=['A','B','C','D','E','F','G','H','I','J','K','L'];
  var g=0,t=0;
  letras.forEach(function(l){
    var s1=document.querySelector('[name="g_'+l+'_1"]');
    var s2=document.querySelector('[name="g_'+l+'_2"]');
    var s3=document.querySelector('[name="g_'+l+'_3"]');
    if(s1&&s1.value&&s2&&s2.value)g++;
    if(s3&&s3.value)t++;
  });
  var bg=document.getElementById('badge-grupos');
  var bt=document.getElementById('badge-terceros');
  var btn=document.getElementById('btn-sig');
  bg.textContent='Grupos: '+g+'/12';
  bg.className='badge '+(g===12?'badge-ok':'badge-fail');
  bt.textContent='Mejores terceros: '+t+'/8';
  bt.className='badge '+(t===8?'badge-ok':'badge-fail');
  btn.disabled=!(g===12&&t===8);
}
document.querySelectorAll('select').forEach(function(s){s.addEventListener('change',validate);});
validate();
</script>
</body></html>
"""

# ---------------------------------------------------------------------------
# ELIMINATORIAS FORM
# ---------------------------------------------------------------------------
ELIM_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eliminatorias – Porra Mundial 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;850;900&display=swap" rel="stylesheet">
""" + _BASE_STYLE + """
<style>
  .phase{display:none;padding:22px 0;border-top:1px solid var(--line);}
  .phase.active{display:block;animation:fadein .3s;}
  @keyframes fadein{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
  .phase h3{margin:0 0 6px;color:var(--pitch-dark);font-size:1.05rem;}
  .phase p.sub{margin:0 0 14px;color:var(--muted);font-size:.88rem;}
  .teams-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:9px;}
  .chk{display:none;}
  .lbl{display:block;padding:10px 8px;border:2px solid var(--line);border-radius:8px;
    text-align:center;cursor:pointer;font-weight:750;font-size:.85rem;
    background:#fff;transition:border-color .12s,background .12s;}
  .chk:checked+.lbl{border-color:var(--pitch);background:#e6f5ee;color:var(--pitch-dark);}
  .chk:disabled+.lbl{opacity:.4;cursor:not-allowed;}
  .counter{display:inline-block;padding:5px 13px;border-radius:20px;font-weight:850;
    font-size:.85rem;margin-bottom:14px;background:#fde8e4;color:#8b2215;}
  .counter.ok{background:#d4edda;color:#0f5132;}
  .pichichi-wrap{max-width:360px;margin-top:10px;}
  .sticky-btn{position:sticky;bottom:0;background:#fff;border-top:2px solid var(--line);
    padding:16px 20px;text-align:center;}
</style>
</head><body>
{{ topbar | safe }}
<main class="shell">
  <section class="card">
    <div class="section-header">
      <p class="eyebrow">Paso 2 de 2</p>
      <h2>Fase Eliminatoria</h2>
    </div>
    <div class="body-pad">
      <form method="post" id="form-elim">

        <!-- 1. OCTAVOS: 32 clasificados → elige 16 -->
        <div class="phase active" id="sec-octavos">
          <h3>1. Octavos de Final</h3>
          <p class="sub">De los 32 clasificados, elige los <strong>16</strong> que pasan a octavos.</p>
          <div class="counter" id="cnt-oct">0 / 16 seleccionados</div>
          <div class="teams-grid" id="grid-octavos">
            {% for eq in clasificados %}
            <span>
              <input type="checkbox" name="octavos" value="{{ eq }}"
                     id="oct_{{ loop.index }}" class="chk chk-oct">
              <label class="lbl" for="oct_{{ loop.index }}">{{ eq }}</label>
            </span>
            {% endfor %}
          </div>
        </div>

        <!-- 2. CUARTOS: de 16 → elige 8 -->
        <div class="phase" id="sec-cuartos">
          <h3>2. Cuartos de Final</h3>
          <p class="sub">De los 16 de octavos, elige los <strong>8</strong> que pasan a cuartos.</p>
          <div class="counter" id="cnt-cua">0 / 8 seleccionados</div>
          <div class="teams-grid" id="grid-cuartos"></div>
        </div>

        <!-- 3. SEMIS -->
        <div class="phase" id="sec-semis">
          <h3>3. Semifinales</h3>
          <p class="sub">De los 8 de cuartos, elige los <strong>4</strong> semifinalistas.</p>
          <div class="counter" id="cnt-sem">0 / 4 seleccionados</div>
          <div class="teams-grid" id="grid-semis"></div>
        </div>

        <!-- 4. FINAL: de 4 semis → elige 2 -->
        <div class="phase" id="sec-final">
          <h3>4. La Final</h3>
          <p class="sub">De los 4 semifinalistas, elige los <strong>2</strong> finalistas.</p>
          <div class="counter" id="cnt-fin">0 / 2 seleccionados</div>
          <div class="teams-grid" id="grid-final"></div>
        </div>

        <!-- 5. CAMPEÓN + SUBCAMPEÓN + PICHICHI -->
        <div class="phase" id="sec-campeon">
          <h3>5. ¿Quién gana el Mundial?</h3>
          <p class="sub">Elige al campeón. El otro finalista será el subcampeón automáticamente.</p>
          <div class="teams-grid" id="grid-campeon"></div>
          <input type="hidden" name="subcampeon" id="inp-sub">

          <h3 style="margin-top:26px;">6. Pichichi (máximo goleador)</h3>
          <p class="sub">Escribe el nombre del jugador que crees que será el máximo goleador.</p>
          <div class="pichichi-wrap">
            <input type="text" name="pichichi" placeholder="Ej: Kylian Mbappé" required>
          </div>
        </div>

        <div class="sticky-btn">
          <button type="submit" id="btn-fin" class="btn btn-primary"
                  style="display:none;font-size:1.05rem;padding:14px 32px;">
            🎉 Guardar predicción
          </button>
        </div>
      </form>
    </div>
  </section>
</main>
<script>
// Generic phase setup: when max checkboxes selected, build next phase
function setupPhase(srcClass, destGridId, destPrefix, nameAttr, max, cntId, nextSecId) {
  var boxes = Array.from(document.querySelectorAll('.' + srcClass));
  function refresh() {
    var sel = boxes.filter(function(c){return c.checked;}).map(function(c){return c.value;});
    var cnt = document.getElementById(cntId);
    cnt.textContent = sel.length + ' / ' + max + ' seleccionados';
    cnt.className = 'counter' + (sel.length >= max ? ' ok' : '');
    if (sel.length >= max) {
      boxes.forEach(function(c){if(!c.checked) c.disabled = true;});
      buildGrid(sel, destGridId, destPrefix, nameAttr, nextSecId);
    } else {
      boxes.forEach(function(c){c.disabled = false;});
      clearFrom(nextSecId);
    }
  }
  boxes.forEach(function(b){b.addEventListener('change', refresh);});
}

function buildGrid(teams, gridId, prefix, nameAttr, sectionId) {
  var grid = document.getElementById(gridId);
  if (!grid) return;
  grid.innerHTML = '';
  var isRadio = (nameAttr === 'campeon');
  teams.forEach(function(eq, i) {
    var id = prefix + '_' + i;
    grid.innerHTML +=
      '<span>' +
      '<input type="' + (isRadio ? 'radio' : 'checkbox') + '" ' +
             'name="' + nameAttr + '" value="' + eq + '" ' +
             'id="' + id + '" class="chk chk-' + nameAttr + '">' +
      '<label class="lbl" for="' + id + '">' + eq + '</label>' +
      '</span>';
  });
  var sec = document.getElementById(sectionId);
  if (sec) sec.classList.add('active');

  if (nameAttr === 'cuartos') setupPhase('chk-cuartos','grid-semis','sem','semis',8,'cnt-cua','sec-semis');
  if (nameAttr === 'semis')   setupPhase('chk-semis','grid-final','fin','final',4,'cnt-sem','sec-final');
  if (nameAttr === 'final')   setupPhase('chk-final','grid-campeon','camp','campeon',2,'cnt-fin','sec-campeon');
  if (nameAttr === 'campeon') {
    Array.from(document.querySelectorAll('.chk-campeon')).forEach(function(r){
      r.addEventListener('change', function(){
        var finalists = Array.from(document.querySelectorAll('.chk-final'))
          .filter(function(c){return c.checked;}).map(function(c){return c.value;});
        document.getElementById('inp-sub').value =
          finalists.find(function(f){return f !== r.value;}) || '';
        document.getElementById('btn-fin').style.display = 'inline-block';
      });
    });
  }
}

function clearFrom(sectionId) {
  var order = ['sec-cuartos','sec-semis','sec-final','sec-campeon'];
  var idx = order.indexOf(sectionId);
  if (idx < 0) return;
  for (var i = idx; i < order.length; i++) {
    document.getElementById(order[i]).classList.remove('active');
  }
  document.getElementById('btn-fin').style.display = 'none';
}

// Boot: octavos picks 16 from the 32 classified
setupPhase('chk-oct', 'grid-cuartos', 'cua', 'cuartos', 16, 'cnt-oct', 'sec-cuartos');
</script>
</body></html>
"""

# ---------------------------------------------------------------------------
# VER PREDICCIÓN
# ---------------------------------------------------------------------------
VER_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Predicción – Porra Mundial 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;850;900&display=swap" rel="stylesheet">
""" + _BASE_STYLE + """
<style>
  .groups-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin-bottom:32px;}
  .gcard{border:1px solid var(--line);border-radius:8px;overflow:hidden;}
  .gcard-hd{background:var(--pitch);color:#fff;padding:8px 12px;font-weight:850;font-size:.88rem;}
  .gcard-bd{padding:10px 12px;}
  .pos{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:.88rem;font-weight:700;}
  .pos-1{color:var(--pitch);}
  .pos-2{color:var(--blue);}
  .pos-3{color:#c97d4d;}
  .rounds{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px;margin-bottom:28px;}
  .round-block h4{margin:0 0 10px;color:var(--pitch-dark);}
  .tags{display:flex;flex-wrap:wrap;gap:6px;}
  .tag{padding:5px 10px;border-radius:6px;border:1px solid var(--line);
    font-size:.82rem;font-weight:750;background:#f8fbf9;}
  .finale{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;
    background:#f3faf6;border-radius:10px;padding:22px;text-align:center;}
  .finale-block small{display:block;color:var(--muted);font-weight:850;font-size:.76rem;
    text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;}
  .finale-block strong{font-size:1.1rem;color:var(--pitch-dark);}
  .finale-block.champion strong{font-size:1.35rem;color:var(--pitch);}
</style>
</head><body>
{{ topbar | safe }}
<main class="shell">
  <section class="card">
    <div class="section-header">
      <p class="eyebrow">Predicción de</p>
      <h2>{{ name }}</h2>
    </div>
    <div class="body-pad">
      <h3 style="color:var(--pitch-dark);margin:0 0 14px">Fase de Grupos</h3>
      <div class="groups-grid">
        {% for letra in 'ABCDEFGHIJKL' %}
        {% set p1 = pred_grupos.get('g_' ~ letra ~ '_1','—') %}
        {% set p2 = pred_grupos.get('g_' ~ letra ~ '_2','—') %}
        {% set p3 = pred_grupos.get('g_' ~ letra ~ '_3','') %}
        <div class="gcard">
          <div class="gcard-hd">Grupo {{ letra }}</div>
          <div class="gcard-bd">
            <div class="pos pos-1">1º {{ p1 }}</div>
            <div class="pos pos-2">2º {{ p2 }}</div>
            {% if p3 %}<div class="pos pos-3">3º {{ p3 }}</div>{% endif %}
          </div>
        </div>
        {% endfor %}
      </div>

      <h3 style="color:var(--pitch-dark);margin:0 0 14px">Fase Eliminatoria</h3>
      <div class="rounds">
        {% for ronda, label in [('octavos','Octavos'),('cuartos','Cuartos'),('semis','Semifinales'),('final','Final')] %}
        {% set equipos = pred_elim.get(ronda,[]) %}
        {% if equipos %}
        <div class="round-block">
          <h4>{{ label }}</h4>
          <div class="tags">
            {% for eq in equipos %}<span class="tag">{{ eq }}</span>{% endfor %}
          </div>
        </div>
        {% endif %}
        {% endfor %}
      </div>

      <div class="finale">
        <div class="finale-block">
          <small>Subcampeón</small>
          <strong>{{ pred_elim.get('subcampeon','—') }}</strong>
        </div>
        <div class="finale-block champion">
          <small>🏆 Campeón Mundial</small>
          <strong>{{ pred_elim.get('campeon','—') }}</strong>
        </div>
        <div class="finale-block">
          <small>⚽ Pichichi</small>
          <strong>{{ pred_elim.get('pichichi','—') }}</strong>
        </div>
      </div>
    </div>
  </section>
</main></body></html>
"""


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _logged_in():
    return bool(session.get("participant_id"))

def _require_login():
    return redirect(url_for("public.welcome"))

def _render_welcome(**kwargs):
    return render_template_string(WELCOME_TEMPLATE, topbar=_topbar(), **kwargs)

def _render_ranking(standings):
    uid = session.get("participant_id")
    has_pred = False
    if uid:
        try:
            p = get_storage().get_participant_by_id(uid)
            pred = p.get("prediction", {}) if p else {}
            has_pred = bool(pred.get("grupos") or pred.get("eliminatorias"))
        except Exception:
            pass
    return render_template_string(
        RANKING_TEMPLATE,
        topbar=_topbar(show_logout=_logged_in()),
        standings=standings,
        current_user=session.get("participant_name"),
        has_prediction=has_pred,
        session=session,
    )


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@public_bp.route("/")
def welcome():
    if _logged_in():
        return redirect(url_for("public.ranking"))
    return _render_welcome()


@public_bp.post("/entrar")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return _render_welcome(login_error="Introduce email y PIN.")
    try:
        participant = get_storage().get_participant_by_email(email)
    except Exception as exc:
        return _render_welcome(login_error=f"Error de conexión: {exc}")
    if not participant or not participant.get("password_hash"):
        return _render_welcome(login_error="No encontramos ese email. ¿Quizá te registraste con otro?")
    if not check_password_hash(participant["password_hash"], password):
        return _render_welcome(login_error="El PIN no coincide.")
    session["participant_id"] = participant["id"]
    session["participant_name"] = participant["name"]
    session["participant_email"] = participant["email"]
    pred = participant.get("prediction", {})
    if not pred.get("grupos"):
        return redirect(url_for("public.grupos_fase"))
    return redirect(url_for("public.ranking"))


@public_bp.post("/registro")
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or not password:
        return _render_welcome(register_error="Completa nombre, email y PIN.")
    if len(password) < 4:
        return _render_welcome(register_error="El PIN debe tener al menos 4 caracteres.", suggested_name=name)
    try:
        storage = get_storage()
        if storage.get_participant_by_email(email):
            return _render_welcome(register_error="Ese email ya está registrado.", suggested_name=name)
        password_hash = generate_password_hash(password)
        storage.create_participant(name, email, password_hash)
        participant = storage.get_participant_by_email(email)
    except Exception as exc:
        return _render_welcome(register_error=f"Error al registrar: {exc}", suggested_name=name)
    if not participant:
        return _render_welcome(register_error="Registro OK pero error al iniciar sesión. Intenta entrar con tu email y PIN.", suggested_name=name)
    session["participant_id"] = participant["id"]
    session["participant_name"] = participant["name"]
    session["participant_email"] = participant["email"]
    return redirect(url_for("public.grupos_fase"))


@public_bp.route("/salir")
def logout():
    session.clear()
    return redirect(url_for("public.welcome"))


@public_bp.route("/ranking")
def ranking():
    try:
        storage = get_storage()
        participants = storage.load_participants()
        results = storage.load_results()
    except Exception:
        participants, results = {}, {}
    standings = build_standings(participants, results)
    # attach id to each row so ranking links work
    try:
        all_p = get_storage().load_participants_full()
        id_map = {p["name"]: p["id"] for p in all_p}
        for row in standings:
            row["id"] = id_map.get(row["name"], "")
    except Exception:
        for row in standings:
            row["id"] = ""
    return _render_ranking(standings)


@public_bp.route("/prediccion/grupos", methods=["GET", "POST"])
def grupos_fase():
    if not _logged_in():
        return _require_login()
    storage = get_storage()
    if request.method == "POST":
        grupos_data = {k: v for k, v in request.form.items()}
        try:
            p = storage.get_participant_by_id(session["participant_id"])
            pred = p.get("prediction", {}) if p else {}
            pred["grupos"] = grupos_data
            storage.update_prediction(session["participant_id"], pred)
        except Exception as exc:
            pass
        return redirect(url_for("public.eliminatorias_fase"))

    saved = {}
    try:
        p = storage.get_participant_by_id(session["participant_id"])
        if p:
            saved = (p.get("prediction") or {}).get("grupos", {})
    except Exception:
        pass

    return render_template_string(
        GRUPOS_TEMPLATE,
        topbar=_topbar(show_logout=True),
        groups=GROUPS,
        teams=TEAMS,
        saved=saved,
    )


@public_bp.route("/prediccion/eliminatorias", methods=["GET", "POST"])
def eliminatorias_fase():
    if not _logged_in():
        return _require_login()
    storage = get_storage()

    if request.method == "POST":
        elim_data = {
            "octavos": request.form.getlist("octavos"),
            "cuartos": request.form.getlist("cuartos"),
            "semis": request.form.getlist("semis"),
            "final": request.form.getlist("final"),
            "campeon": request.form.get("campeon"),
            "subcampeon": request.form.get("subcampeon"),
            "pichichi": request.form.get("pichichi"),
        }
        try:
            p = storage.get_participant_by_id(session["participant_id"])
            pred = p.get("prediction", {}) if p else {}
            pred["eliminatorias"] = elim_data
            storage.update_prediction(session["participant_id"], pred)
        except Exception:
            pass
        return redirect(url_for("public.ranking"))

    # Build clasificados from groups prediction
    clasificados = []
    try:
        p = storage.get_participant_by_id(session["participant_id"])
        if p:
            grupos = (p.get("prediction") or {}).get("grupos", {})
            seen = set()
            for letra in "ABCDEFGHIJKL":
                for pos in ("1", "2", "3"):
                    eq = grupos.get(f"g_{letra}_{pos}", "")
                    if eq and eq not in seen:
                        clasificados.append(eq)
                        seen.add(eq)
    except Exception:
        pass

    if not clasificados:
        return redirect(url_for("public.grupos_fase"))

    return render_template_string(
        ELIM_TEMPLATE,
        topbar=_topbar(show_logout=True),
        clasificados=clasificados,
    )


@public_bp.route("/prediccion/ver/<participant_id>")
def ver_prediccion(participant_id):
    try:
        p = get_storage().get_participant_by_id(participant_id)
    except Exception:
        return redirect(url_for("public.ranking"))
    if not p:
        return redirect(url_for("public.ranking"))
    pred = p.get("prediction") or {}
    return render_template_string(
        VER_TEMPLATE,
        topbar=_topbar(show_logout=_logged_in()),
        name=p["name"],
        pred_grupos=pred.get("grupos", {}),
        pred_elim=pred.get("eliminatorias", {}),
    )


@public_bp.route("/health")
def health():
    return {"status": "ok"}
