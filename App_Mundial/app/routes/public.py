from flask import Blueprint, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.data.tournament import GROUPS, TEAMS
from app.services.scoring import build_standings
from app.storage import get_storage


public_bp = Blueprint("public", __name__)

WELCOME_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Porra Mundial 2026</title>
  <style>
    :root { --ink:#2c3e50; --muted:#6b7b75; --line:#dbe7e1; --wash:#f2f9f5; --pitch:#198754; --pitch-dark:#0f5132; --gold:#d4af37; }
    * { box-sizing: border-box; }
    body { margin:0; min-height:100vh; background:var(--wash); color:var(--ink); padding-top:116px; font-family:Poppins, Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
    .topbar { position:fixed; top:0; left:0; right:0; z-index:20; display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:18px; padding:18px clamp(18px,4vw,48px); color:white; background:linear-gradient(135deg,var(--pitch-dark),var(--pitch)); border-radius:0 0 38px 38px; box-shadow:0 12px 28px rgba(25,135,84,.25); }
    .brand { display:flex; align-items:center; justify-content:center; gap:12px; font-weight:850; text-decoration:none; color:inherit; text-align:center; }
    .mark { display:grid; place-items:center; width:44px; height:44px; border-radius:50%; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35); color:white; }
    .brand small { display:block; color:rgba(255,255,255,.78); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav:last-child { justify-content:flex-end; }
    .nav a, .button { border:0; border-radius:8px; padding:11px 18px; background:white; color:var(--pitch-dark); font-weight:800; text-decoration:none; box-shadow:0 6px 14px rgba(15,81,50,.12); }
    .button { width:100%; min-height:50px; background:var(--pitch); color:white; cursor:pointer; transition:transform .18s ease, box-shadow .18s ease; }
    .button:hover { transform:translateY(-1px); box-shadow:0 8px 18px rgba(25,135,84,.28); }
    .shell { display:grid; gap:22px; width:min(1120px, calc(100% - 32px)); margin:0 auto; padding:34px 0 64px; }
    .welcome-card { overflow:hidden; background:white; border-radius:18px; box-shadow:0 18px 44px rgba(44,62,80,.08); }
    .hero { display:grid; grid-template-columns:minmax(0,1fr) 260px; gap:26px; align-items:center; padding:clamp(26px,5vw,44px); color:var(--ink); background:linear-gradient(180deg,#ffffff,#f8fffb); border-bottom:1px solid var(--line); }
    .eyebrow { margin:0 0 8px; color:var(--pitch); font-size:.78rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
    h1 { margin:0 0 12px; max-width:720px; color:var(--pitch-dark); font-size:clamp(2rem,4.7vw,4.1rem); line-height:1.02; }
    h2 { margin:0; color:var(--pitch-dark); font-size:1.35rem; }
    .lead { max-width:660px; margin:0; color:var(--muted); font-size:1.08rem; line-height:1.55; }
    .trophy { display:grid; place-items:center; min-height:180px; border-radius:16px; color:white; background:linear-gradient(145deg,var(--pitch-dark),var(--pitch)); box-shadow:inset 0 0 0 1px rgba(255,255,255,.16); }
    .trophy span { font-size:4.8rem; line-height:1; }
    .trophy strong { display:block; margin-top:10px; font-size:1rem; letter-spacing:.08em; text-transform:uppercase; }
    .auth { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:0; }
    form { display:grid; gap:14px; padding:28px; background:white; border-right:1px solid var(--line); }
    form.accent { border-right:0; box-shadow:inset 5px 0 0 var(--pitch); }
    form .eyebrow { color:var(--muted); }
    label { color:var(--muted); font-weight:850; }
    input { width:100%; min-height:50px; padding:10px 13px; border:1px solid var(--line); border-radius:8px; color:var(--ink); font:inherit; }
    .hint { margin:0; color:var(--muted); font-size:.92rem; line-height:1.45; }
    input:focus { outline:3px solid rgba(15,107,79,.16); border-color:var(--pitch); }
    .error { margin:0; color:#a33a2a; font-weight:750; }
    @media (max-width:820px) { body { padding-top:138px; } .topbar, .hero, .auth { grid-template-columns:1fr; } .brand { order:-1; } .nav, .nav:last-child { justify-content:center; } form, form.accent { border-right:0; border-top:1px solid var(--line); } .trophy { min-height:130px; } }
  </style>
</head>
<body>
  <header class="topbar">
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a></nav>
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>PORRA MUNDIAL 2026<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.ranking') }}">Clasificación</a></nav>
  </header>
  <main class="shell">
    <section class="welcome-card">
      <div class="hero">
        <div>
          <p class="eyebrow">Elecnor Sistemas</p>
          <h1>Bienvenido a la porra del Mundial</h1>
          <p class="lead">Registra tu nombre, prepara tus predicciones y sigue la clasificación con tus compañeros durante todo el torneo.</p>
        </div>
        <div class="trophy" aria-hidden="true"><div><span>🏆</span><strong>Mundial 2026</strong></div></div>
      </div>
      <div class="auth">
        <form method="post" action="{{ url_for('public.login') }}">
          <div><p class="eyebrow">Acceso</p><h2>Ya participo</h2></div>
          <label for="login-email">Email</label>
          <input id="login-email" name="email" type="email" autocomplete="email" required>
          <label for="login-password">PIN o contraseña</label>
          <input id="login-password" name="password" type="password" autocomplete="current-password" required>
          {% if login_error %}<p class="error">{{ login_error }}</p>{% endif %}
          <button class="button" type="submit">Entrar</button>
        </form>
        <form class="accent" method="post" action="{{ url_for('public.register') }}">
          <div><p class="eyebrow">Registro</p><h2>Nuevo participante</h2></div>
          <label for="register-name">Nombre</label>
          <input id="register-name" name="name" type="text" autocomplete="name" value="{{ suggested_name or '' }}" required>
          <label for="register-email">Email</label>
          <input id="register-email" name="email" type="email" autocomplete="email" required>
          <label for="register-password">PIN o contraseña</label>
          <input id="register-password" name="password" type="password" minlength="4" autocomplete="new-password" required>
          <p class="hint">Usa un PIN de al menos 4 caracteres. Te servirá para volver a entrar y editar tu predicción.</p>
          {% if register_error %}<p class="error">{{ register_error }}</p>{% endif %}
          <button class="button" type="submit">Registrarme</button>
        </form>
      </div>
    </section>
  </main>
</body>
</html>
"""

RANKING_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clasificación - Porra Mundial 2026</title>
  <style>
    :root { --ink:#2c3e50; --muted:#6b7b75; --line:#dbe7e1; --wash:#f2f9f5; --pitch:#198754; --pitch-dark:#0f5132; --gold:#d4af37; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; padding-top:116px; background:var(--wash); color:var(--ink); font-family:Poppins, Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
    .topbar { position:fixed; top:0; left:0; right:0; z-index:20; display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:18px; padding:18px clamp(18px,4vw,48px); color:white; background:linear-gradient(135deg,var(--pitch-dark),var(--pitch)); border-radius:0 0 38px 38px; box-shadow:0 12px 28px rgba(25,135,84,.25); }
    a { color:inherit; text-decoration:none; }
    .brand { display:flex; align-items:center; justify-content:center; gap:12px; font-weight:850; text-align:center; }
    .mark { display:grid; place-items:center; width:44px; height:44px; border-radius:50%; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35); color:white; }
    .brand small { display:block; color:rgba(255,255,255,.78); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav:last-child { justify-content:flex-end; }
    .nav a, .button { border:0; border-radius:8px; padding:11px 18px; background:white; color:var(--pitch-dark); font-weight:800; box-shadow:0 6px 14px rgba(15,81,50,.12); }
    .button { background:var(--pitch); color:white; }
    .shell { width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:34px 0 64px; }
    .panel { padding:28px; background:white; border:1px solid var(--line); border-radius:18px; box-shadow:0 18px 44px rgba(44,62,80,.08); }
    .heading { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:22px; }
    .eyebrow { margin:0 0 8px; color:var(--muted); font-size:.78rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
    h1 { margin:0; color:var(--pitch-dark); font-size:clamp(2rem,4vw,3.4rem); }
    ol { display:grid; gap:8px; padding:0; margin:0; list-style:none; }
    li { display:grid; grid-template-columns:44px minmax(0,1fr) auto; gap:12px; align-items:center; min-height:58px; padding:10px 12px; border:1px solid var(--line); border-radius:10px; }
    .rank { display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:#e8f2ed; color:var(--pitch); font-weight:900; }
    .points { color:var(--gold); font-weight:900; }
    .empty { padding:34px 24px; border:1px dashed var(--line); border-radius:12px; color:var(--muted); font-weight:750; text-align:center; }
    @media (max-width:820px) { body { padding-top:138px; } .topbar { grid-template-columns:1fr; } .brand { order:-1; } .nav, .nav:last-child { justify-content:center; } .heading { align-items:flex-start; flex-direction:column; } }
  </style>
</head>
<body>
  <header class="topbar">
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a></nav>
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>PORRA MUNDIAL 2026<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.ranking') }}">Clasificación</a>{% if session.get('participant_name') %}<a href="{{ url_for('public.logout') }}">Salir</a>{% endif %}</nav>
  </header>
  <main class="shell">
    <section class="panel">
      <div class="heading">
        <div><p class="eyebrow">Clasificación</p><h1>Ranking general</h1></div>
        <a class="button" href="{{ url_for('public.welcome') }}">Participar</a>
      </div>
      {% if standings %}
        <ol>
          {% for row in standings %}
            <li><span class="rank">{{ loop.index }}</span><strong>{{ row.name }}</strong><span class="points">{{ row.points }} pts</span></li>
          {% endfor %}
        </ol>
      {% else %}
        <div class="empty">Todavía no hay participantes. Regístrate para abrir la clasificación.</div>
      {% endif %}
    </section>
  </main>
</body>
</html>
"""


@public_bp.route("/")
def welcome():
    return render_template_string(WELCOME_TEMPLATE)


@public_bp.post("/entrar")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return render_template_string(WELCOME_TEMPLATE, login_error="Introduce email y PIN.")

    participant = get_storage().get_participant_by_email(email)
    if not participant or not participant.get("password_hash"):
        return render_template_string(
            WELCOME_TEMPLATE,
            login_error="No encontramos ese participante. Puedes registrarlo ahora.",
        )

    if not check_password_hash(participant["password_hash"], password):
        return render_template_string(WELCOME_TEMPLATE, login_error="El PIN no coincide.")

    session["participant_id"] = participant["id"]
    session["participant_name"] = participant["name"]
    session["participant_email"] = participant["email"]
    return redirect(url_for("public.ranking"))


@public_bp.post("/registro")
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or not password:
        return render_template_string(WELCOME_TEMPLATE, register_error="Completa nombre, email y PIN.")
    if len(password) < 4:
        return render_template_string(WELCOME_TEMPLATE, register_error="El PIN debe tener al menos 4 caracteres.", suggested_name=name)

    storage = get_storage()
    if storage.get_participant_by_email(email):
        return render_template_string(WELCOME_TEMPLATE, register_error="Ese email ya está registrado.", suggested_name=name)

    password_hash = generate_password_hash(password)
    storage.create_participant(name, email, password_hash)
    participant = storage.get_participant_by_email(email)
    session["participant_id"] = participant["id"]
    session["participant_name"] = participant["name"]
    session["participant_email"] = participant["email"]
    return redirect(url_for("public.ranking"))


@public_bp.route("/salir")
def logout():
    session.clear()
    return redirect(url_for("public.welcome"))


@public_bp.route("/ranking")
def ranking():
    storage = get_storage()
    participants = storage.load_participants()
    results = storage.load_results()
    standings = build_standings(participants, results)

    return render_template_string(
        RANKING_TEMPLATE,
        groups=GROUPS,
        teams=TEAMS,
        participants=participants,
        results=results,
        standings=standings,
    )


@public_bp.route("/health")
def health():
    return {"status": "ok"}
