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
    :root {
      --ink:#10251d;
      --muted:#60756d;
      --line:#d9e6df;
      --wash:#eef7f2;
      --paper:#ffffff;
      --pitch:#138455;
      --pitch-dark:#073f2b;
      --pitch-deep:#052d21;
      --gold:#d8b24a;
      --blue:#215f9f;
    }
    * { box-sizing:border-box; }
    body {
      margin:0;
      min-height:100vh;
      padding-top:126px;
      color:var(--ink);
      font-family:Poppins, Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
      background:
        linear-gradient(90deg, rgba(7,63,43,.05) 1px, transparent 1px),
        linear-gradient(180deg, rgba(7,63,43,.05) 1px, transparent 1px),
        linear-gradient(180deg, #f8fbf9 0%, var(--wash) 58%, #e7f2ec 100%);
      background-size:64px 64px, 64px 64px, auto;
    }
    .topbar {
      position:fixed;
      top:0;
      left:0;
      right:0;
      z-index:20;
      display:grid;
      grid-template-columns:1fr auto 1fr;
      align-items:center;
      gap:18px;
      padding:18px clamp(18px,4vw,56px);
      color:white;
      background:
        linear-gradient(120deg, rgba(255,255,255,.08), transparent 34%),
        linear-gradient(135deg,var(--pitch-deep),var(--pitch));
      border-radius:0 0 42px 42px;
      box-shadow:0 18px 36px rgba(7,63,43,.22);
    }
    .brand { display:flex; align-items:center; justify-content:center; gap:12px; font-weight:850; text-decoration:none; color:inherit; text-align:center; }
    .mark { display:grid; place-items:center; width:46px; height:46px; border-radius:50%; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.34); color:white; box-shadow:inset 0 0 0 5px rgba(255,255,255,.08); }
    .brand small { display:block; color:rgba(255,255,255,.78); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav:last-child { justify-content:flex-end; }
    .nav a, .button { border:0; border-radius:8px; padding:12px 20px; background:white; color:var(--pitch-dark); font-weight:850; text-decoration:none; box-shadow:0 8px 16px rgba(5,45,33,.14); }
    .button { width:100%; min-height:52px; background:var(--pitch); color:white; cursor:pointer; transition:transform .18s ease, box-shadow .18s ease; }
    .button:hover { transform:translateY(-1px); box-shadow:0 12px 22px rgba(19,132,85,.28); }
    .shell { width:min(1220px, calc(100% - 32px)); margin:0 auto; padding:34px 0 64px; }
    .stadium {
      overflow:hidden;
      border:1px solid rgba(16,37,29,.08);
      border-radius:8px;
      background:var(--paper);
      box-shadow:0 24px 70px rgba(7,63,43,.14);
    }
    .hero {
      display:grid;
      grid-template-columns:minmax(0, 1fr) minmax(320px, 430px);
      gap:34px;
      align-items:stretch;
      padding:clamp(28px,5vw,54px);
      background:
        linear-gradient(90deg, rgba(19,132,85,.08) 1px, transparent 1px),
        linear-gradient(180deg, #ffffff 0%, #f6fbf8 100%);
      background-size:42px 42px, auto;
      border-bottom:1px solid var(--line);
    }
    .copy { display:flex; flex-direction:column; justify-content:center; min-height:330px; }
    .eyebrow { margin:0 0 10px; color:var(--pitch); font-size:.78rem; font-weight:900; letter-spacing:.12em; text-transform:uppercase; }
    h1 { margin:0 0 16px; max-width:760px; color:var(--pitch-dark); font-size:clamp(2.6rem,5vw,5.2rem); line-height:.96; letter-spacing:0; }
    h2 { margin:0; color:var(--pitch-dark); font-size:1.45rem; }
    .lead { max-width:710px; margin:0; color:var(--muted); font-size:1.12rem; line-height:1.58; }
    .flagline { display:flex; flex-wrap:wrap; gap:8px; margin:24px 0 0; }
    .flagline img { width:34px; height:24px; object-fit:cover; border-radius:3px; box-shadow:0 1px 4px rgba(16,37,29,.18); }
    .pitch-card {
      position:relative;
      min-height:330px;
      padding:22px;
      color:white;
      border-radius:8px;
      overflow:hidden;
      background:
        linear-gradient(90deg, rgba(255,255,255,.10) 1px, transparent 1px),
        linear-gradient(180deg, rgba(255,255,255,.08) 1px, transparent 1px),
        linear-gradient(135deg, #075136 0%, #138455 58%, #215f9f 100%);
      background-size:44px 44px, 44px 44px, auto;
      box-shadow:inset 0 0 0 1px rgba(255,255,255,.18), 0 22px 42px rgba(7,63,43,.2);
    }
    .pitch-card::before {
      content:"";
      position:absolute;
      inset:28px;
      border:2px solid rgba(255,255,255,.34);
      border-radius:8px;
    }
    .pitch-card::after {
      content:"";
      position:absolute;
      left:50%;
      top:50%;
      width:118px;
      height:118px;
      transform:translate(-50%,-50%);
      border:2px solid rgba(255,255,255,.34);
      border-radius:50%;
    }
    .scoreboard { position:relative; z-index:1; display:grid; gap:14px; }
    .score-top { display:flex; justify-content:space-between; align-items:center; gap:12px; }
    .score-top span { padding:7px 10px; border-radius:8px; background:rgba(255,255,255,.14); font-size:.78rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
    .match { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:10px; margin-top:24px; padding:14px; border-radius:8px; background:rgba(5,45,33,.58); backdrop-filter:blur(5px); }
    .team { display:grid; gap:6px; justify-items:center; font-weight:900; }
    .team img { width:42px; height:28px; object-fit:cover; border-radius:3px; }
    .versus { color:var(--gold); font-weight:950; }
    .groups { position:absolute; z-index:1; left:22px; right:22px; bottom:22px; display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
    .group-chip { min-height:72px; padding:10px; border-radius:8px; background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.16); }
    .group-chip strong { display:block; margin-bottom:6px; color:#fff3c4; font-size:.82rem; }
    .group-chip span { display:block; color:rgba(255,255,255,.82); font-size:.76rem; line-height:1.35; }
    .auth { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); background:white; }
    form { display:grid; gap:14px; padding:30px; background:white; border-right:1px solid var(--line); }
    form.accent { border-right:0; box-shadow:inset 5px 0 0 var(--pitch); }
    form .eyebrow { color:var(--muted); }
    label { color:var(--muted); font-weight:850; }
    input { width:100%; min-height:52px; padding:11px 13px; border:1px solid var(--line); border-radius:8px; color:var(--ink); font:inherit; background:#fbfdfc; }
    .hint { margin:0; color:var(--muted); font-size:.92rem; line-height:1.45; }
    input:focus { outline:3px solid rgba(15,107,79,.16); border-color:var(--pitch); }
    .error { margin:0; color:#a33a2a; font-weight:750; }
    @media (max-width:920px) {
      body { padding-top:148px; }
      .topbar, .hero, .auth { grid-template-columns:1fr; }
      .brand { order:-1; }
      .nav, .nav:last-child { justify-content:center; }
      .copy { min-height:auto; }
      form, form.accent { border-right:0; border-top:1px solid var(--line); }
    }
    @media (max-width:560px) {
      .shell { width:calc(100% - 20px); padding-top:18px; }
      .hero, form { padding:22px; }
      .groups { grid-template-columns:1fr; position:relative; left:auto; right:auto; bottom:auto; margin-top:18px; }
      .pitch-card { min-height:auto; }
      .match { margin-top:12px; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a></nav>
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>PORRA MUNDIAL 2026<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.ranking') }}">Clasificación</a></nav>
  </header>
  <main class="shell">
    <section class="stadium">
      <div class="hero">
        <div class="copy">
          <p class="eyebrow">Elecnor Sistemas</p>
          <h1>La porra del Mundial empieza aquí</h1>
          <p class="lead">Regístrate, entra al marcador y compite con tus compañeros durante todo el torneo. Una experiencia sencilla, rápida y con sabor a Mundial.</p>
          <div class="flagline" aria-hidden="true">
            <img src="https://flagcdn.com/w40/es.png" alt="">
            <img src="https://flagcdn.com/w40/ar.png" alt="">
            <img src="https://flagcdn.com/w40/br.png" alt="">
            <img src="https://flagcdn.com/w40/fr.png" alt="">
            <img src="https://flagcdn.com/w40/de.png" alt="">
            <img src="https://flagcdn.com/w40/us.png" alt="">
            <img src="https://flagcdn.com/w40/mx.png" alt="">
            <img src="https://flagcdn.com/w40/ca.png" alt="">
          </div>
        </div>
        <aside class="pitch-card" aria-label="Resumen visual del torneo">
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
    :root {
      --ink:#10251d;
      --muted:#60756d;
      --line:#d9e6df;
      --wash:#eef7f2;
      --paper:#ffffff;
      --pitch:#138455;
      --pitch-dark:#073f2b;
      --pitch-deep:#052d21;
      --gold:#d8b24a;
      --silver:#c6d0ca;
      --bronze:#c97d4d;
    }
    * { box-sizing:border-box; }
    body {
      margin:0;
      min-height:100vh;
      padding-top:126px;
      background:
        linear-gradient(90deg, rgba(7,63,43,.05) 1px, transparent 1px),
        linear-gradient(180deg, rgba(7,63,43,.05) 1px, transparent 1px),
        linear-gradient(180deg, #f8fbf9 0%, var(--wash) 58%, #e7f2ec 100%);
      background-size:64px 64px, 64px 64px, auto;
      color:var(--ink);
      font-family:Poppins, Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    }
    .topbar {
      position:fixed;
      top:0;
      left:0;
      right:0;
      z-index:20;
      display:grid;
      grid-template-columns:1fr auto 1fr;
      align-items:center;
      gap:18px;
      padding:18px clamp(18px,4vw,56px);
      color:white;
      background:
        linear-gradient(120deg, rgba(255,255,255,.08), transparent 34%),
        linear-gradient(135deg,var(--pitch-deep),var(--pitch));
      border-radius:0 0 42px 42px;
      box-shadow:0 18px 36px rgba(7,63,43,.22);
    }
    a { color:inherit; text-decoration:none; }
    .brand { display:flex; align-items:center; justify-content:center; gap:12px; font-weight:850; text-align:center; }
    .mark { display:grid; place-items:center; width:46px; height:46px; border-radius:50%; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.34); color:white; box-shadow:inset 0 0 0 5px rgba(255,255,255,.08); }
    .brand small { display:block; color:rgba(255,255,255,.78); font-weight:700; }
    .nav { display:flex; gap:8px; flex-wrap:wrap; }
    .nav:last-child { justify-content:flex-end; }
    .nav a, .button { border:0; border-radius:8px; padding:12px 20px; background:white; color:var(--pitch-dark); font-weight:850; box-shadow:0 8px 16px rgba(5,45,33,.14); }
    .button { background:var(--pitch); color:white; }
    .shell { width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:34px 0 64px; }
    .leaderboard {
      overflow:hidden;
      border:1px solid rgba(16,37,29,.08);
      border-radius:8px;
      background:var(--paper);
      box-shadow:0 24px 70px rgba(7,63,43,.14);
    }
    .ranking-hero {
      display:grid;
      grid-template-columns:minmax(0,1fr) auto;
      gap:24px;
      align-items:end;
      padding:34px;
      color:white;
      background:
        linear-gradient(90deg, rgba(255,255,255,.10) 1px, transparent 1px),
        linear-gradient(180deg, rgba(255,255,255,.08) 1px, transparent 1px),
        linear-gradient(135deg, #073f2b 0%, #138455 68%, #215f9f 100%);
      background-size:46px 46px, 46px 46px, auto;
    }
    .eyebrow { margin:0 0 10px; color:rgba(255,255,255,.75); font-size:.78rem; font-weight:900; letter-spacing:.12em; text-transform:uppercase; }
    h1 { margin:0; font-size:clamp(2.2rem,4.6vw,4.4rem); line-height:.98; letter-spacing:0; }
    .summary { display:grid; grid-template-columns:repeat(2, minmax(110px,1fr)); gap:10px; min-width:260px; }
    .stat { padding:14px; border-radius:8px; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.18); }
    .stat strong { display:block; font-size:1.6rem; }
    .stat span { color:rgba(255,255,255,.78); font-size:.8rem; font-weight:800; text-transform:uppercase; }
    .ranking-body { padding:30px; }
    ol { display:grid; gap:10px; padding:0; margin:0; list-style:none; }
    li {
      display:grid;
      grid-template-columns:52px minmax(0,1fr) auto;
      gap:14px;
      align-items:center;
      min-height:68px;
      padding:12px 14px;
      border:1px solid var(--line);
      border-radius:8px;
      background:#fbfdfc;
    }
    li:nth-child(1) { border-color:rgba(216,178,74,.55); background:linear-gradient(90deg, rgba(216,178,74,.14), #fff); }
    li:nth-child(2) { border-color:rgba(198,208,202,.75); }
    li:nth-child(3) { border-color:rgba(201,125,77,.55); }
    .rank { display:grid; place-items:center; width:40px; height:40px; border-radius:50%; background:#e8f2ed; color:var(--pitch); font-weight:950; }
    li:nth-child(1) .rank { background:var(--gold); color:#2d2206; }
    li:nth-child(2) .rank { background:var(--silver); color:#23342c; }
    li:nth-child(3) .rank { background:var(--bronze); color:white; }
    .name strong { display:block; color:var(--pitch-dark); font-size:1.05rem; }
    .name span { color:var(--muted); font-size:.9rem; }
    .points { padding:8px 11px; border-radius:8px; background:#eef7f2; color:var(--pitch-dark); font-weight:950; white-space:nowrap; }
    .empty { padding:38px 24px; border:1px dashed var(--line); border-radius:8px; color:var(--muted); font-weight:750; text-align:center; }
    @media (max-width:820px) {
      body { padding-top:148px; }
      .topbar, .ranking-hero { grid-template-columns:1fr; }
      .brand { order:-1; }
      .nav, .nav:last-child { justify-content:center; }
      .summary { min-width:0; }
      li { grid-template-columns:44px minmax(0,1fr); }
      .points { grid-column:2; width:max-content; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <nav class="nav"><a href="{{ url_for('public.welcome') }}">Inicio</a></nav>
    <a class="brand" href="{{ url_for('public.welcome') }}"><span class="mark">26</span><span>PORRA MUNDIAL 2026<small>Elecnor Sistemas</small></span></a>
    <nav class="nav"><a href="{{ url_for('public.ranking') }}">Clasificación</a>{% if session.get('participant_name') %}<a href="{{ url_for('public.logout') }}">Salir</a>{% endif %}</nav>
  </header>
  <main class="shell">
    <section class="leaderboard">
      <div class="ranking-hero">
        <div><p class="eyebrow">Clasificación</p><h1>Ranking general</h1></div>
        <div class="summary" aria-label="Resumen de la porra">
          <div class="stat"><strong>{{ standings|length }}</strong><span>Participantes</span></div>
          <div class="stat"><strong>2026</strong><span>Mundial</span></div>
        </div>
      </div>
      <div class="ranking-body">
        {% if standings %}
          <ol>
            {% for row in standings %}
              <li>
                <span class="rank">{{ loop.index }}</span>
                <span class="name"><strong>{{ row.name }}</strong><span>Participante Elecnor</span></span>
                <span class="points">{{ row.points }} pts</span>
              </li>
            {% endfor %}
          </ol>
        {% else %}
          <div class="empty">Todavía no hay participantes. Regístrate para abrir la clasificación.</div>
        {% endif %}
      </div>
    </section>
  </main>
</body>
</html>
"""


@public_bp.route("/")
def welcome():
    if session.get("participant_name"):
        return redirect(url_for("public.ranking"))
    return render_template_string(WELCOME_TEMPLATE)


@public_bp.post("/entrar")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return render_template_string(WELCOME_TEMPLATE, login_error="Introduce email y PIN.")

    try:
        participant = get_storage().get_participant_by_email(email)
    except Exception:
        return render_template_string(
            WELCOME_TEMPLATE,
            login_error="Error de conexión. Inténtalo de nuevo en un momento.",
        )

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
        return render_template_string(
            WELCOME_TEMPLATE,
            register_error="El PIN debe tener al menos 4 caracteres.",
            suggested_name=name,
        )

    try:
        storage = get_storage()
        if storage.get_participant_by_email(email):
            return render_template_string(
                WELCOME_TEMPLATE,
                register_error="Ese email ya está registrado.",
                suggested_name=name,
            )

        password_hash = generate_password_hash(password)
        storage.create_participant(name, email, password_hash)
        participant = storage.get_participant_by_email(email)
    except Exception as exc:
        return render_template_string(
            WELCOME_TEMPLATE,
            register_error=f"[DEBUG] {type(exc).__name__}: {exc}",
            suggested_name=name,
        )

    if not participant:
        return render_template_string(
            WELCOME_TEMPLATE,
            register_error="Registro completado pero no se pudo iniciar sesión. Intenta entrar con tu email y PIN.",
            suggested_name=name,
        )

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
    try:
        storage = get_storage()
        participants = storage.load_participants()
        results = storage.load_results()
    except Exception:
        participants, results = {}, {}
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
    from flask import current_app
    url = current_app.config.get("SUPABASE_URL") or ""
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    return {
        "status": "ok",
        "supabase_url": url[:40] + "..." if len(url) > 40 else url or "NOT SET",
        "service_role_key_prefix": key[:12] + "..." if len(key) > 12 else key or "NOT SET",
        "storage_backend": current_app.config.get("STORAGE_BACKEND"),
    }
