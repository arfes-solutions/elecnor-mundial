from flask import Blueprint, redirect, render_template_string, request, url_for

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
    :root { --ink:#15201d; --muted:#65736f; --line:#dfe7e3; --wash:#f3f7f4; --pitch:#0f6b4f; --blue:#1d4f91; }
    * { box-sizing: border-box; }
    body { margin:0; min-height:100vh; background:var(--wash); color:var(--ink); font-family:Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
    .topbar { display:flex; justify-content:space-between; align-items:center; gap:18px; padding:16px clamp(18px,4vw,48px); background:rgba(255,255,255,.92); border-bottom:1px solid var(--line); }
    .brand { display:flex; align-items:center; gap:12px; font-weight:850; text-decoration:none; color:inherit; }
    .mark { display:grid; place-items:center; width:42px; height:42px; border-radius:50%; background:var(--pitch); color:white; }
    .brand small { display:block; color:var(--muted); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav a, .button { border:1px solid var(--line); border-radius:999px; padding:10px 15px; background:white; color:inherit; font-weight:800; text-decoration:none; }
    .button { width:100%; min-height:48px; background:var(--pitch); border-color:var(--pitch); color:white; cursor:pointer; }
    .shell { display:grid; gap:22px; width:min(1080px, calc(100% - 32px)); margin:0 auto; padding:48px 0 64px; }
    .hero { padding:clamp(32px,6vw,62px); border-radius:8px; color:white; background:linear-gradient(120deg, rgba(15,107,79,.96), rgba(29,79,145,.9)); }
    .eyebrow { margin:0 0 8px; color:rgba(255,255,255,.78); font-size:.78rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
    h1 { margin:0 0 14px; max-width:720px; font-size:clamp(2.3rem,6vw,5rem); line-height:.98; }
    h2 { margin:0; font-size:1.35rem; }
    .lead { max-width:620px; margin:0; color:rgba(255,255,255,.78); font-size:1.07rem; line-height:1.55; }
    .auth { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:18px; }
    form { display:grid; gap:14px; padding:24px; background:white; border:1px solid var(--line); border-radius:8px; }
    form.accent { border-color:rgba(15,107,79,.28); box-shadow:inset 4px 0 0 var(--pitch); }
    form .eyebrow { color:var(--muted); }
    label { color:var(--muted); font-weight:850; }
    input { width:100%; min-height:48px; padding:10px 12px; border:1px solid var(--line); border-radius:8px; color:var(--ink); font:inherit; }
    input:focus { outline:3px solid rgba(15,107,79,.16); border-color:var(--pitch); }
    .error { margin:0; color:#a33a2a; font-weight:750; }
    @media (max-width:760px) { .topbar, .auth { align-items:flex-start; grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>Porra Mundial<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a><a href="{{ url_for('public.ranking') }}">Clasificación</a></nav>
  </header>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Elecnor Sistemas</p>
      <h1>Porra Mundial 2026</h1>
      <p class="lead">Entra con tu nombre para ver tu porra o regístrate para empezar la predicción.</p>
    </section>
    <section class="auth">
      <form method="post" action="{{ url_for('public.login') }}">
        <div><p class="eyebrow">Acceso</p><h2>Ya participo</h2></div>
        <label for="login-name">Nombre</label>
        <input id="login-name" name="name" type="text" autocomplete="name" required>
        {% if login_error %}<p class="error">{{ login_error }}</p>{% endif %}
        <button class="button" type="submit">Entrar</button>
      </form>
      <form class="accent" method="post" action="{{ url_for('public.register') }}">
        <div><p class="eyebrow">Registro</p><h2>Nuevo participante</h2></div>
        <label for="register-name">Nombre</label>
        <input id="register-name" name="name" type="text" autocomplete="name" value="{{ suggested_name or '' }}" required>
        {% if register_error %}<p class="error">{{ register_error }}</p>{% endif %}
        <button class="button" type="submit">Registrarme</button>
      </form>
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
    :root { --ink:#15201d; --muted:#65736f; --line:#dfe7e3; --wash:#f3f7f4; --pitch:#0f6b4f; --gold:#c69324; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:var(--wash); color:var(--ink); font-family:Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
    .topbar { display:flex; justify-content:space-between; align-items:center; gap:18px; padding:16px clamp(18px,4vw,48px); background:white; border-bottom:1px solid var(--line); }
    a { color:inherit; text-decoration:none; }
    .brand { display:flex; align-items:center; gap:12px; font-weight:850; }
    .mark { display:grid; place-items:center; width:42px; height:42px; border-radius:50%; background:var(--pitch); color:white; }
    .brand small { display:block; color:var(--muted); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav a, .button { border:1px solid var(--line); border-radius:999px; padding:10px 15px; background:white; font-weight:800; }
    .button { background:var(--pitch); color:white; border-color:var(--pitch); }
    .shell { width:min(1100px, calc(100% - 32px)); margin:0 auto; padding:40px 0 64px; }
    .panel { padding:24px; background:white; border:1px solid var(--line); border-radius:8px; }
    .heading { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:22px; }
    .eyebrow { margin:0 0 8px; color:var(--muted); font-size:.78rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
    h1 { margin:0; font-size:clamp(2rem,4vw,3.4rem); }
    ol { display:grid; gap:8px; padding:0; margin:0; list-style:none; }
    li { display:grid; grid-template-columns:44px minmax(0,1fr) auto; gap:12px; align-items:center; min-height:54px; padding:8px 12px; border:1px solid var(--line); border-radius:8px; }
    .rank { display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:#e8f2ed; color:var(--pitch); font-weight:900; }
    .points { color:var(--gold); font-weight:900; }
    .empty { padding:24px; border:1px dashed var(--line); border-radius:8px; color:var(--muted); font-weight:750; }
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>Porra Mundial<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a><a href="{{ url_for('public.ranking') }}">Clasificación</a></nav>
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
    name = request.form.get("name", "").strip()
    if not name:
        return render_template_string(WELCOME_TEMPLATE, login_error="Introduce tu nombre.")

    participants = get_storage().load_participants()
    if name not in participants:
        return render_template_string(
            WELCOME_TEMPLATE,
            login_error="No encontramos ese participante. Puedes registrarlo ahora.",
            suggested_name=name,
        )

    return redirect(url_for("public.ranking"))


@public_bp.post("/registro")
def register():
    name = request.form.get("name", "").strip()
    if not name:
        return render_template_string(WELCOME_TEMPLATE, register_error="Introduce tu nombre.")

    storage = get_storage()
    participants = storage.load_participants()
    if name not in participants:
        storage.save_participant(name, {"grupos": {}, "eliminatorias": {}})

    return redirect(url_for("public.ranking"))


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
