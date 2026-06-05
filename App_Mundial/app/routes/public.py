from flask import Blueprint, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.data.tournament import GROUPS, TEAMS
from app.services.scoring import build_standings
from app.storage import get_storage


public_bp = Blueprint("public", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _grupos_fmt():
    """Convert GROUPS/TEAMS to the original {letra: [(iso, name)]} format."""
    return {
        letra: [(TEAMS[tid]["flag"], TEAMS[tid]["name"]) for tid in team_ids]
        for letra, team_ids in GROUPS.items()
    }


def _logged_in():
    return session.get("authenticated", False)


# ---------------------------------------------------------------------------
# ORIGINAL HTML TEMPLATE (from legacy_app.py, adapted url_for + auth views)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Porra Mundial 2026 · Elecnor Sistemas</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏆</text></svg>">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f2f9f5; color: #2c3e50; padding-top: 110px; }
        .header-banner {
            position: fixed; top: 0; left: 0; right: 0; z-index: 1050;
            background: linear-gradient(135deg, #0f5132 0%, #198754 100%);
            color: white; padding: 1rem 1.5rem;
            border-radius: 0 0 40px 40px;
            box-shadow: 0 4px 15px rgba(25, 135, 84, 0.3);
        }
        .header-banner h1 { font-size: clamp(1.2rem, 3vw, 1.6rem); font-weight: 700; letter-spacing: 1px; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); margin: 0; }
        .header-banner p { font-size: clamp(0.7rem, 1.5vw, 0.9rem); font-weight: 400; margin: 0; opacity: 0.9; }
        .card { border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: none; background-color: rgba(255,255,255,0.98); }
        .table-custom-header { background-color: #0f5132 !important; color: white !important; }
        .puntos-oro { color: #d4af37; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
        .btn-success-custom { background-color: #198754; border: none; border-radius: 8px; transition: all 0.3s ease; }
        .btn-success-custom:hover:not(:disabled) { background-color: #146c43; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(25,135,84,0.3); }
        .btn-success-custom:disabled { opacity: 0.5; cursor: not-allowed; background-color: #6c757d; }
        .btn-outline-custom { color: #0f5132; border-color: #0f5132; border-radius: 8px; }
        .btn-outline-custom:hover { background-color: #0f5132; color: white; }
        select option { font-weight: bold; color: #2c3e50; }
        select option:disabled { font-weight: normal; color: #adb5bd; font-style: italic; }
        .team-checkbox { display: none; }
        .team-label { cursor: pointer; border: 2px solid #dee2e6; border-radius: 8px; padding: 10px; transition: all 0.2s; display: block; text-align: center; background: white; font-weight: 600; }
        .team-checkbox:checked + .team-label { border-color: #198754; background-color: #e8f5e9; color: #0f5132; box-shadow: 0 4px 8px rgba(25,135,84,0.2); transform: scale(1.02); }
        .team-checkbox:disabled + .team-label { opacity: 0.5; cursor: not-allowed; }
        .fase-section { display: none; }
        .fase-active { display: block; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="header-banner">
        <div class="d-flex flex-wrap justify-content-between align-items-center mx-auto gap-2" style="max-width: 1400px;">
            <div class="d-flex gap-2">
                <a href="{{ url_for('public.welcome') }}" class="btn btn-light text-success fw-bold px-3">Inicio</a>
                <button type="button" class="btn btn-light text-success fw-bold px-3" data-bs-toggle="modal" data-bs-target="#modalReglas">
                    Reglas
                </button>
            </div>
            <div class="text-center flex-grow-1 d-none d-md-block">
                <h1>PORRA MUNDIAL 2026</h1>
                <p>Elecnor Sistemas</p>
            </div>
            <div class="d-flex gap-2">
                <a href="{{ url_for('public.ver_grupos') }}" class="btn btn-light text-success fw-bold px-3">Grupos</a>
                <a href="{{ url_for('public.ver_horarios') }}" class="btn btn-light text-success fw-bold px-3">Horarios</a>
            </div>
        </div>
    </div>

    <div class="container-fluid px-4 mb-5">

        {% if vista == 'inicio' %}
        <div class="card p-2 p-md-4 mx-auto" style="max-width: 1200px;">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
                    <h3 class="card-title m-0 fw-bold text-success">Clasificación General</h3>
                    <a href="{{ url_for('public.nueva_prediccion') }}" class="btn btn-success-custom text-white fw-bold px-4 py-2">➕ Añadir predicción</a>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead class="table-custom-header">
                            <tr>
                                <th scope="col" class="py-3 rounded-start-2">Pos</th>
                                <th scope="col" class="py-3">Nombre</th>
                                <th scope="col" class="text-center py-3">Puntos</th>
                                <th scope="col" class="text-end py-3 rounded-end-2">Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for jug in clasificacion %}
                            <tr>
                                <td class="fw-bold fs-5">{{ loop.index }}º</td>
                                <td class="fw-bold fs-5">{{ jug.name }}</td>
                                <td class="text-center fw-bold fs-4 puntos-oro">{{ jug.points }} pts</td>
                                <td class="text-end">
                                    <a href="{{ url_for('public.ver_prediccion', participant_id=jug.id) }}" class="btn btn-sm btn-outline-custom px-3">Ver predicción</a>
                                </td>
                            </tr>
                            {% else %}
                            <tr><td colspan="4" class="text-center py-5 text-muted fs-5">El campo está vacío. ¡Sé el primero en participar! ⚽</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        {% elif vista == 'login_register' %}
        <div class="row justify-content-center mt-2">
            <div class="col-md-5 col-lg-4">
                <div class="card p-4">
                    <h4 class="fw-bold text-success border-bottom pb-3 mb-1 text-center">⚽ Porra Mundial 2026</h4>
                    <p class="text-center text-muted small mb-4">Acceso exclusivo para empleados de Elecnor Sistemas.</p>
                    {% if auth_error %}
                    <div class="alert alert-danger py-2">{{ auth_error }}</div>
                    {% endif %}
                    <form method="POST" action="{{ url_for('public.login') }}">
                        <div class="mb-3">
                            <label class="form-label fw-bold text-success fs-5">Usuario</label>
                            <input type="text" name="username" class="form-control form-control-lg border-success text-center"
                                   required autocomplete="username">
                        </div>
                        <div class="mb-4">
                            <label class="form-label fw-bold text-success fs-5">Contraseña</label>
                            <input type="password" name="password" class="form-control form-control-lg border-success text-center"
                                   required autocomplete="current-password" placeholder="••••••••">
                        </div>
                        <button type="submit" class="btn btn-success-custom text-white fw-bold w-100 py-2 fs-5">Entrar →</button>
                    </form>
                </div>
            </div>
        </div>

        {% elif vista == 'nuevo_nombre' %}
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-5">
                <div class="card p-2 p-md-4 mt-4">
                    <div class="card-body">
                        <h3 class="mb-4 fw-bold text-success border-bottom pb-3 text-center">➕ Añadir predicción</h3>
                        {% if nombre_error %}
                        <div class="alert alert-danger py-2">{{ nombre_error }}</div>
                        {% endif %}
                        <form method="POST">
                            <div class="mb-4 p-3 mt-3">
                                <label for="nombre" class="form-label fw-bold fs-5 text-success text-center w-100">Introduce tu nombre:</label>
                                <input type="text" autocomplete="off" class="form-control form-control-lg text-center shadow-sm border-success"
                                       id="nombre" name="nombre" required placeholder="Ej: Benito Martínez"
                                       value="{{ suggested_name or '' }}">
                                <p class="text-muted small text-center mt-2">Así aparecerás en la clasificación.</p>
                            </div>
                            <div class="d-flex justify-content-between mt-4 pt-3 border-top">
                                <a href="{{ url_for('public.welcome') }}" class="btn btn-light border px-4 py-2 fw-bold text-secondary">Cancelar</a>
                                <button type="submit" class="btn btn-success-custom text-white px-5 py-2 fw-bold fs-5">Siguiente →</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        {% elif vista == 'ver_eliminatorias' %}
        <div class="card p-3 p-md-4 mx-auto mb-4 bg-transparent border-0 shadow-none" style="max-width: 1400px;">
            <div class="d-flex justify-content-between align-items-center border-bottom border-success pb-3 mb-4">
                <h3 class="m-0 fw-bold text-success">⚔️ Fase Eliminatoria</h3>
                <a href="{{ url_for('public.welcome') }}" class="btn btn-outline-secondary fw-bold px-4">Clasificación actual</a>
            </div>
            {% for ronda_label, partidos in rondas.items() %}
            <h5 class="fw-bold text-success mb-3 mt-2">{{ ronda_label }}</h5>
            <div class="row mb-4">
                {% for p in partidos %}
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card shadow-sm border-0 {% if p.is_live %}border-warning border-2{% endif %}">
                        <div class="card-body p-3">
                            <div class="text-center text-muted small mb-2 fw-bold border-bottom pb-2 d-flex justify-content-between">
                                <span>{{ p.fecha }} - {{ p.hora }}</span>
                                {% if p.is_live %}
                                    <span class="badge bg-danger">🔴 EN VIVO</span>
                                {% elif p.is_finished %}
                                    <span class="badge bg-secondary">Finalizado</span>
                                {% else %}
                                    <span class="badge bg-light text-muted border">Pendiente</span>
                                {% endif %}
                            </div>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                {% set home_name = p.home.name if p.home.name and p.home.name not in ('?','None') else 'Por determinar' %}
                                {% set away_name = p.away.name if p.away.name and p.away.name not in ('?','None') else 'Por determinar' %}
                                <div class="text-end" style="width:40%;">
                                    <span class="fw-bold">{{ home_name }}</span>
                                    {% if p.home.flag and home_name != 'Por determinar' %}<img src="https://flagcdn.com/w20/{{ p.home.flag }}.png" width="20" class="ms-1">{% endif %}
                                </div>
                                <div class="text-center fw-bold fs-5" style="width:20%;">
                                    {% if p.is_finished or p.is_live %}
                                        <span class="text-success">{{ p.home_score }} - {{ p.away_score }}</span>
                                    {% else %}
                                        <span class="text-muted">vs</span>
                                    {% endif %}
                                </div>
                                <div class="text-start" style="width:40%;">
                                    {% if p.away.flag and away_name != 'Por determinar' %}<img src="https://flagcdn.com/w20/{{ p.away.flag }}.png" width="20" class="me-1">{% endif %}
                                    <span class="fw-bold">{{ away_name }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>

        {% elif vista == 'ver_grupos' %}
        <div class="card p-3 p-md-4 mx-auto mb-4 bg-transparent border-0 shadow-none" style="max-width: 1400px;">
            <div class="d-flex justify-content-between align-items-center border-bottom border-success pb-3 mb-4">
                <h3 class="m-0 fw-bold text-success">Clasificación de Grupos en Directo</h3>
                <a href="{{ url_for('public.welcome') }}" class="btn btn-outline-secondary fw-bold px-4">← Volver</a>
            </div>
            <div class="row">
                {% for letra, equipos_ordenados in grupos_ordenados.items() %}
                <div class="col-md-6 col-lg-3 mb-4">
                    <div class="card h-100 shadow-sm border-0 bg-light">
                        <div class="card-header bg-success text-white fw-bold text-center py-2">Grupo {{ letra }}</div>
                        <div class="card-body p-2">
                            <div class="d-flex flex-column gap-2">
                                {% for iso, pais, puesto in equipos_ordenados %}
                                <div class="bg-white border rounded px-2 py-2 shadow-sm d-flex align-items-center justify-content-between">
                                    <div class="d-flex align-items-center gap-2">
                                        <img src="https://flagcdn.com/w20/{{ iso }}.png" width="20" alt="{{ pais }}">
                                        <span class="fw-semibold text-dark small">{{ pais }}</span>
                                    </div>
                                    {% if puesto == '1º' %}<span class="badge bg-success shadow-sm">{{ puesto }}</span>
                                    {% elif puesto == '2º' %}<span class="badge bg-primary shadow-sm">{{ puesto }}</span>
                                    {% elif puesto == '3º' %}<span class="badge bg-warning text-dark shadow-sm">{{ puesto }}</span>
                                    {% else %}<span class="badge bg-secondary opacity-25">-</span>{% endif %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        {% elif vista == 'ver_horarios_dinamico' %}
        <div class="card p-3 p-md-4 mx-auto mb-4 bg-transparent border-0 shadow-none" style="max-width: 1400px;">
            <div class="d-flex justify-content-between align-items-center border-bottom border-success pb-3 mb-4">
                <h3 class="m-0 fw-bold text-success">📅 Partidos del Mundial (Hora Peninsular)</h3>
                <a href="{{ url_for('public.welcome') }}" class="btn btn-outline-secondary fw-bold px-4">← Volver</a>
            </div>
            <div class="row">
                {% for sec_key, sec in sections.items() %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm border-0 bg-light">
                        <div class="card-header bg-success text-white fw-bold text-center py-2">{{ sec.label }}</div>
                        <div class="card-body p-3">
                            <div class="d-flex flex-column gap-3">
                                {% for p in sec.partidos %}
                                <div class="bg-white border rounded p-2 shadow-sm {% if p.is_live %}border-warning border-2{% endif %}">
                                    <div class="text-center text-muted small mb-2 fw-bold border-bottom pb-1 d-flex justify-content-between align-items-center px-1">
                                        <span class="text-success">{{ p.jornada or p.stage_label }}</span>
                                        <span>{{ p.fecha }} - {{ p.hora }}</span>
                                        {% if p.is_live %}
                                        <span class="badge bg-danger">EN VIVO</span>
                                        {% elif p.is_finished %}
                                        <span class="badge bg-secondary">Finalizado</span>
                                        {% endif %}
                                    </div>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div class="text-end" style="width:40%; font-size:0.9rem;">
                                            <span class="fw-bold">{{ p.home.name }}</span>
                                            {% if p.home.flag %}<img src="https://flagcdn.com/w20/{{ p.home.flag }}.png" width="20" class="ms-1">{% endif %}
                                        </div>
                                        <div class="text-center fw-bold" style="width:20%;">
                                            {% if p.is_finished or p.is_live %}
                                            <span class="text-success fs-5">{{ p.home_score }} - {{ p.away_score }}</span>
                                            {% else %}
                                            <span class="text-secondary">vs</span>
                                            {% endif %}
                                        </div>
                                        <div class="text-start" style="width:40%; font-size:0.9rem;">
                                            {% if p.away.flag %}<img src="https://flagcdn.com/w20/{{ p.away.flag }}.png" width="20" class="me-1">{% endif %}
                                            <span class="fw-bold">{{ p.away.name }}</span>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        {% elif vista == 'ver_horarios' %}
        <div class="card p-3 p-md-4 mx-auto mb-4 bg-transparent border-0 shadow-none" style="max-width: 1400px;">
            <div class="d-flex justify-content-between align-items-center border-bottom border-success pb-3 mb-4">
                <h3 class="m-0 fw-bold text-success">📅 Horarios del Mundial (Hora Peninsular)</h3>
                <a href="{{ url_for('public.welcome') }}" class="btn btn-outline-secondary fw-bold px-4">← Volver</a>
            </div>
            <div class="row">
                {% for letra, partidos in calendario.items() %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm border-0 bg-light">
                        <div class="card-header bg-success text-white fw-bold text-center py-2">Grupo {{ letra }}</div>
                        <div class="card-body p-3">
                            <div class="d-flex flex-column gap-3">
                                {% for p in partidos %}
                                <div class="bg-white border rounded p-2 shadow-sm">
                                    <div class="text-center text-muted small mb-2 fw-bold border-bottom pb-1">
                                        <span class="text-success">{{ p.jornada }}</span> • {{ p.fecha }} - {{ p.hora }}
                                    </div>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div class="text-end" style="width:40%;font-size:0.9rem;">
                                            <span class="fw-bold">{{ p.eq1[1] }}</span>
                                            <img src="https://flagcdn.com/w20/{{ p.eq1[0] }}.png" width="20" alt="{{ p.eq1[1] }}" class="ms-1">
                                        </div>
                                        <div class="text-center fw-bold text-secondary" style="width:20%;">vs</div>
                                        <div class="text-start" style="width:40%;font-size:0.9rem;">
                                            <img src="https://flagcdn.com/w20/{{ p.eq2[0] }}.png" width="20" alt="{{ p.eq2[1] }}" class="me-1">
                                            <span class="fw-bold">{{ p.eq2[1] }}</span>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        {% elif vista == 'ver_prediccion' %}
        <div class="card p-3 p-md-4 mx-auto" style="max-width: 1200px;">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-4">
                    <h3 class="m-0 fw-bold text-success">Predicción de {{ nombre }}</h3>
                    <a href="{{ url_for('public.welcome') }}" class="btn btn-outline-secondary fw-bold px-4">← Volver</a>
                </div>
                <h5 class="fw-bold text-secondary mb-3">Fase de Grupos</h5>
                <div class="row g-3 mb-5">
                    {% for letra in ['A','B','C','D','E','F','G','H','I','J','K','L'] %}
                        {% set p1 = predicciones.get('grupos',{}).get('g_' ~ letra ~ '_1', '') %}
                        {% set p2 = predicciones.get('grupos',{}).get('g_' ~ letra ~ '_2', '') %}
                        {% set p3 = predicciones.get('grupos',{}).get('g_' ~ letra ~ '_3', '') %}
                        <div class="col-6 col-md-4 col-lg-3">
                            <div class="card shadow-sm h-100 border-0 bg-light">
                                <div class="card-header bg-success text-white text-center fw-bold py-2">Grupo {{ letra }}</div>
                                <div class="card-body p-2 text-center small">
                                    <div class="fw-bold text-dark mb-1"><span class="text-success me-1">1º</span> {{ p1 or '—' }}</div>
                                    <div class="fw-bold text-dark mb-1"><span class="text-primary me-1">2º</span> {{ p2 or '—' }}</div>
                                    {% if p3 %}<div class="fw-bold text-muted"><span class="text-warning me-1">3º</span> {{ p3 }}</div>{% endif %}
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
                <h5 class="fw-bold text-secondary mb-3 border-top pt-4">Rondas Finales</h5>
                <div class="row g-4">
                    <div class="col-md-6">
                        <h6 class="bg-success text-white p-2 rounded text-center fw-bold">Octavos de Final</h6>
                        <div class="d-flex flex-wrap justify-content-center gap-1">
                            {% for eq in predicciones.get('eliminatorias',{}).get('octavos', []) %}
                                <span class="badge bg-white text-dark border border-secondary p-2">{{ eq }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="bg-success text-white p-2 rounded text-center fw-bold">Cuartos de Final</h6>
                        <div class="d-flex flex-wrap justify-content-center gap-1">
                            {% for eq in predicciones.get('eliminatorias',{}).get('cuartos', []) %}
                                <span class="badge bg-white text-dark border border-secondary p-2">{{ eq }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="bg-success text-white p-2 rounded text-center fw-bold">Semifinales</h6>
                        <div class="d-flex flex-wrap justify-content-center gap-2">
                            {% for eq in predicciones.get('eliminatorias',{}).get('semis', []) %}
                                <span class="badge bg-white text-dark border border-secondary p-2 fs-6">{{ eq }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="bg-success text-white p-2 rounded text-center fw-bold">La Final</h6>
                        <div class="d-flex flex-wrap justify-content-center gap-3">
                            {% for eq in predicciones.get('eliminatorias',{}).get('final', []) %}
                                <span class="badge bg-white text-dark border border-success p-2 fs-5">{{ eq }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                <div class="row mt-5 justify-content-center text-center bg-light p-4 rounded-4 shadow-sm mx-1">
                    <div class="col-md-4 mb-3 mb-md-0 border-end border-2">
                        <h6 class="text-muted fw-bold mb-2">SUBCAMPEÓN</h6>
                        <h4 class="fw-bold text-secondary m-0">{{ predicciones.get('eliminatorias',{}).get('subcampeon', '-') }}</h4>
                    </div>
                    <div class="col-md-4 mb-3 mb-md-0 border-end border-2">
                        <h6 class="text-warning fw-bold mb-2">🏆 CAMPEÓN MUNDIAL</h6>
                        <h3 class="fw-bold text-success m-0">{{ predicciones.get('eliminatorias',{}).get('campeon', '-') }}</h3>
                    </div>
                    <div class="col-md-4">
                        <h6 class="text-primary fw-bold mb-2">⚽ PICHICHI</h6>
                        <h4 class="fw-bold text-dark m-0">{{ predicciones.get('eliminatorias',{}).get('pichichi', '-') }}</h4>
                    </div>
                </div>
            </div>
        </div>

        {% elif vista == 'fase_grupos' %}
        <div class="card p-3 mb-4 shadow-sm border-start border-success border-4 mx-auto" style="max-width:1200px;background-color:#fff;">
            <h5 class="fw-bold text-success mb-2">📋 Reglas de Clasificación de la Fase de Grupos</h5>
            <p class="text-muted small mb-2">
                En el Mundial 2026, se clasifican para dieciseisavos de final los dos primeros equipos de cada grupo y además los 8 mejores terceros clasificados en general.<br>Por tanto:
            </p>
            <ul class="text-muted small" style="line-height:1.6;">
                <li>Debes seleccionar obligatoriamente el <strong>1º y 2º puesto</strong> de cada uno de los 12 grupos.</li>
                <li>Debes elegir exactamente a <strong>8 equipos como mejores terceros</strong> en total.</li>
            </ul>
            <p class="text-muted small mb-0">El botón para avanzar al final de la página se habilitará automáticamente cuando completes todos los requisitos.</p>
        </div>

        <form method="POST" class="mx-auto" style="max-width:1400px;">
            <div class="row">
                {% for letra, equipos in grupos.items() %}
                <div class="col-md-6 col-lg-3 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-header bg-success text-white fw-bold text-center fs-5">Grupo {{ letra }}</div>
                        <div class="card-body bg-light p-3">
                            <div class="d-flex flex-column gap-1 mb-3">
                                {% for iso, pais in equipos %}
                                <div class="bg-white border rounded px-2 py-1 shadow-sm d-flex align-items-center gap-2">
                                    <img src="https://flagcdn.com/w20/{{ iso }}.png" width="20" alt="{{ pais }}">
                                    <span class="fw-semibold text-dark small">{{ pais }}</span>
                                </div>
                                {% endfor %}
                            </div>
                            <hr class="my-2">
                            <div class="mb-2">
                                <label class="form-label text-muted small fw-bold mb-1">1º Puesto <span class="text-danger">*</span></label>
                                <select class="form-select form-select-sm fw-bold border-secondary text-secondary" name="g_{{ letra }}_1" required>
                                    <option value="" disabled selected hidden>Elegir 1º...</option>
                                    {% for iso, pais in equipos %}
                                    <option value="{{ pais }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_1') == pais }}>{{ pais }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-2">
                                <label class="form-label text-muted small fw-bold mb-1">2º Puesto <span class="text-danger">*</span></label>
                                <select class="form-select form-select-sm fw-bold border-secondary text-secondary" name="g_{{ letra }}_2" required>
                                    <option value="" disabled selected hidden>Elegir 2º...</option>
                                    {% for iso, pais in equipos %}
                                    <option value="{{ pais }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_2') == pais }}>{{ pais }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-2">
                                <label class="form-label text-muted small fw-bold mb-1">Mejor 3º (Opcional)</label>
                                <select class="form-select form-select-sm border-secondary text-secondary select-tercero" name="g_{{ letra }}_3">
                                    <option value="">Ninguno / Eliminado</option>
                                    {% for iso, pais in equipos %}
                                    <option value="{{ pais }}" {{ 'selected' if saved.get('g_' ~ letra ~ '_3') == pais }}>{{ pais }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="card p-4 mt-2 shadow-sm text-center mx-auto mb-5" style="max-width:1200px;">
                <div class="mb-3 d-flex justify-content-center gap-3 flex-wrap">
                    <span id="counter-grupos" class="badge bg-danger fs-6 p-2">Grupos: 0 / 12 completados</span>
                    <span id="terceros-counter" class="badge bg-danger fs-6 p-2">Mejores Terceros: 0 / 8 elegidos</span>
                </div>
                <button type="submit" id="btn-siguiente" class="btn btn-success-custom text-white px-5 py-3 fw-bold fs-5 mx-auto" disabled>Continuar</button>
            </div>
        </form>

        <script>
            function validarFormulario() {
                let gruposCompletos = 0, tercerosContados = 0;
                const letras = ['A','B','C','D','E','F','G','H','I','J','K','L'];
                letras.forEach(letra => {
                    const s1 = document.querySelector('select[name="g_' + letra + '_1"]');
                    const s2 = document.querySelector('select[name="g_' + letra + '_2"]');
                    const s3 = document.querySelector('select[name="g_' + letra + '_3"]');
                    const selects = [s1, s2, s3];
                    for (let i = 0; i < selects.length; i++) {
                        for (let j = 0; j < selects[i].options.length; j++) {
                            let opt = selects[i].options[j];
                            if (opt.value === "") continue;
                            let isDisabled = false;
                            for (let k = 0; k < selects.length; k++) {
                                if (i !== k && selects[k].value === opt.value) { isDisabled = true; break; }
                            }
                            opt.disabled = isDisabled;
                        }
                    }
                    if (s1.value !== "" && s2.value !== "") gruposCompletos++;
                    if (s3 && s3.value !== "") tercerosContados++;
                });
                const btnSubmit = document.getElementById('btn-siguiente');
                const lblGrupos = document.getElementById('counter-grupos');
                const lblTerceros = document.getElementById('terceros-counter');
                lblGrupos.innerText = "Grupos: " + gruposCompletos + " / 12 completados";
                lblGrupos.className = (gruposCompletos === 12) ? "badge bg-success fs-6 p-2" : "badge bg-danger fs-6 p-2";
                lblTerceros.innerText = "Mejores Terceros: " + tercerosContados + " / 8 elegidos";
                lblTerceros.className = (tercerosContados === 8) ? "badge bg-success fs-6 p-2" : "badge bg-danger fs-6 p-2";
                btnSubmit.disabled = !(gruposCompletos === 12 && tercerosContados === 8);
            }
            document.addEventListener("DOMContentLoaded", function() {
                document.querySelectorAll("select").forEach(s => s.addEventListener("change", validarFormulario));
                validarFormulario();
            });
        </script>

        {% elif vista == 'eliminatorias' %}
        <div class="card p-4 mx-auto shadow-sm" style="max-width:1200px;">
            <h3 class="fw-bold text-success border-bottom pb-3 text-center">Fase Eliminatoria - {{ nombre }}</h3>
            <p class="text-center text-muted">Selecciona los equipos que avanzan en cada ronda.</p>
            <form method="POST" id="form-eliminatorias">
                <div id="sec-octavos" class="fase-section fase-active mb-5">
                    <h5 class="bg-success text-white p-2 rounded text-center">1. Selecciona 16 equipos para OCTAVOS DE FINAL</h5>
                    <div class="text-center mb-3"><span id="count-octavos" class="badge bg-warning text-dark fs-6">0 / 16 seleccionados</span></div>
                    <div class="row g-2">
                        {% for equipo in clasificados %}
                        <div class="col-4 col-md-3 col-lg-2">
                            <input type="checkbox" name="octavos" value="{{ equipo }}" id="oct_{{ loop.index }}" class="team-checkbox chk-octavos">
                            <label class="team-label text-truncate" for="oct_{{ loop.index }}">{{ equipo }}</label>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <div id="sec-cuartos" class="fase-section mb-5 border-top pt-4">
                    <h5 class="bg-success text-white p-2 rounded text-center">2. Selecciona 8 equipos para CUARTOS DE FINAL</h5>
                    <div class="text-center mb-3"><span id="count-cuartos" class="badge bg-warning text-dark fs-6">0 / 8 seleccionados</span></div>
                    <div class="row g-2" id="grid-cuartos"></div>
                </div>
                <div id="sec-semis" class="fase-section mb-5 border-top pt-4">
                    <h5 class="bg-success text-white p-2 rounded text-center">3. Selecciona 4 equipos para SEMIFINALES</h5>
                    <div class="text-center mb-3"><span id="count-semis" class="badge bg-warning text-dark fs-6">0 / 4 seleccionados</span></div>
                    <div class="row g-2" id="grid-semis"></div>
                </div>
                <div id="sec-final" class="fase-section mb-5 border-top pt-4">
                    <h5 class="bg-success text-white p-2 rounded text-center">4. Selecciona 2 equipos para LA FINAL</h5>
                    <div class="text-center mb-3"><span id="count-final" class="badge bg-warning text-dark fs-6">0 / 2 seleccionados</span></div>
                    <div class="row g-2 justify-content-center" id="grid-final"></div>
                </div>
                <div id="sec-campeon" class="fase-section mb-5 border-top pt-4">
                    <h5 class="bg-warning text-dark p-2 rounded text-center fw-bold">5. ¡Elige al Campeón Mundial!</h5>
                    <div class="row g-2 justify-content-center mb-4" id="grid-campeon"></div>
                    <input type="hidden" name="subcampeon" id="input-subcampeon">
                    <h5 class="bg-primary text-white p-2 rounded text-center mt-4">6. Pichichi del Torneo (Máximo Goleador)</h5>
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <input type="text" name="pichichi" class="form-control form-control-lg text-center" placeholder="Ej: Kylian Mbappé" required>
                        </div>
                    </div>
                </div>
                <div class="text-center mt-4">
                    <button type="submit" id="btn-finalizar" class="btn btn-success-custom text-white px-5 py-3 fw-bold fs-4 w-100 d-none">🎉 Terminar Predicción 🎉</button>
                </div>
            </form>
        </div>

        <script>
            function setupFase(origenClase, destinoGrid, destinoPrefijo, maxSelect, counterId, nextSectionId, nameAttr) {
                const checkboxes = document.querySelectorAll('.' + origenClase);
                checkboxes.forEach(chk => {
                    chk.addEventListener('change', function() {
                        const selected = Array.from(checkboxes).filter(c => c.checked).map(c => c.value);
                        const counter = document.getElementById(counterId);
                        counter.innerText = selected.length + " / " + maxSelect + " seleccionados";
                        if (selected.length >= maxSelect) {
                            counter.className = "badge bg-success fs-6";
                            checkboxes.forEach(c => { if(!c.checked) c.disabled = true; });
                            generarSiguienteFase(selected, destinoGrid, destinoPrefijo, nameAttr, nextSectionId);
                        } else {
                            counter.className = "badge bg-warning text-dark fs-6";
                            checkboxes.forEach(c => c.disabled = false);
                            document.getElementById(nextSectionId).classList.remove('fase-active');
                            limpiarFasesDesde(nextSectionId);
                        }
                    });
                });
            }
            function generarSiguienteFase(equipos, contenedorId, prefijoId, nameAttr, sectionId) {
                if(!contenedorId) return;
                const contenedor = document.getElementById(contenedorId);
                contenedor.innerHTML = '';
                equipos.forEach((equipo, index) => {
                    const type = (nameAttr === 'campeon') ? 'radio' : 'checkbox';
                    contenedor.innerHTML += `
                        <div class="col-6 col-md-3">
                            <input type="${type}" name="${nameAttr}" value="${equipo}" id="${prefijoId}_${index}" class="team-checkbox chk-${nameAttr}">
                            <label class="team-label text-truncate" for="${prefijoId}_${index}">${equipo}</label>
                        </div>`;
                });
                document.getElementById(sectionId).classList.add('fase-active');
                if(nameAttr === 'cuartos') setupFase('chk-cuartos', 'grid-semis', 'sem', 8, 'count-cuartos', 'sec-semis', 'semis');
                if(nameAttr === 'semis') setupFase('chk-semis', 'grid-final', 'fin', 4, 'count-semis', 'sec-final', 'final');
                if(nameAttr === 'final') setupFase('chk-final', 'grid-campeon', 'camp', 2, 'count-final', 'sec-campeon', 'campeon');
                if(nameAttr === 'campeon') {
                    document.querySelectorAll('.chk-campeon').forEach(radio => {
                        radio.addEventListener('change', function() {
                            const finalistas = Array.from(document.querySelectorAll('.chk-final')).filter(c=>c.checked).map(c=>c.value);
                            const sub = finalistas.find(f => f !== this.value);
                            document.getElementById('input-subcampeon').value = sub;
                            document.getElementById('btn-finalizar').classList.remove('d-none');
                        });
                    });
                }
            }
            function limpiarFasesDesde(sectionId) {
                const fases = ['sec-cuartos', 'sec-semis', 'sec-final', 'sec-campeon'];
                const index = fases.indexOf(sectionId);
                if(index !== -1) { for(let i = index; i < fases.length; i++) document.getElementById(fases[i]).classList.remove('fase-active'); }
                document.getElementById('btn-finalizar').classList.add('d-none');
            }
            setupFase('chk-octavos', 'grid-cuartos', 'cua', 16, 'count-octavos', 'sec-cuartos', 'cuartos');
        </script>

        {% endif %}
    </div>

    <!-- MODAL REGLAS -->
    <div class="modal fade" id="modalReglas" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content border-0 shadow">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title fw-bold">📋 Reglas y Puntuaciones</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4 text-dark">
                    <h6 class="fw-bold text-success border-bottom pb-2 mb-3">🌍 Sistema de Clasificación (Mundial 2026)</h6>
                    <p class="small text-muted mb-4">
                        En esta edición compiten 48 selecciones repartidas en 12 grupos. Se clasifican para la ronda de <strong>Dieciseisavos de Final (32 equipos en total):</strong><br>
                        - Los <strong>2 primeros</strong> equipos de cada grupo.<br>
                        - Los <strong>8 mejores terceros</strong> en el cómputo global.
                    </p>
                    <h6 class="fw-bold text-primary border-bottom pb-2 mb-3">🔢 Sistema de Puntuación de la Porra</h6>
                    <ul class="list-group list-group-flush small">
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Fase de Grupos (acertar que un equipo se clasifica)<span class="badge bg-secondary rounded-pill">+1 pt</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Fase de Grupos (acertar también su posición exacta)<span class="badge bg-secondary rounded-pill">+1 pt extra</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Acertar cada equipo en Octavos de Final<span class="badge bg-primary rounded-pill">+3 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Acertar cada equipo en Cuartos de Final<span class="badge bg-primary rounded-pill">+5 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Acertar cada equipo en Semifinales<span class="badge bg-primary rounded-pill">+8 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0">Acertar cada equipo en La Final<span class="badge bg-primary rounded-pill">+12 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0 bg-light mt-2 fw-bold text-secondary">Acertar el Subcampeón<span class="badge bg-warning text-dark rounded-pill">+10 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0 bg-light fw-bold text-success">🏆 Acertar el Campeón Mundial<span class="badge bg-success rounded-pill">+20 pts</span></li>
                        <li class="list-group-item d-flex justify-content-between align-items-center px-0 bg-light fw-bold text-dark">⚽ Acertar el Pichichi (Máximo Goleador)<span class="badge bg-dark rounded-pill">+7 pts</span></li>
                    </ul>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">Entendido</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def _render(vista, **kwargs):
    return render_template_string(
        HTML_TEMPLATE,
        vista=vista,
        authenticated=session.get("authenticated", False),
        **kwargs,
    )


def _generar_calendario():
    return {
        'A': [
            {'jornada':'Jornada 1','eq1':('mx','México'),'eq2':('za','Sudáfrica'),'fecha':'11 Jun','hora':'21:00'},
            {'jornada':'Jornada 1','eq1':('kr','Corea del Sur'),'eq2':('cz','Chequia'),'fecha':'12 Jun','hora':'04:00'},
            {'jornada':'Jornada 2','eq1':('cz','Chequia'),'eq2':('za','Sudáfrica'),'fecha':'18 Jun','hora':'18:00'},
            {'jornada':'Jornada 2','eq1':('mx','México'),'eq2':('kr','Corea del Sur'),'fecha':'19 Jun','hora':'03:00'},
            {'jornada':'Jornada 3','eq1':('za','Sudáfrica'),'eq2':('kr','Corea del Sur'),'fecha':'25 Jun','hora':'03:00'},
            {'jornada':'Jornada 3','eq1':('cz','Chequia'),'eq2':('mx','México'),'fecha':'25 Jun','hora':'03:00'},
        ],
        'B': [
            {'jornada':'Jornada 1','eq1':('ca','Canadá'),'eq2':('ba','Bosnia y Herzegovina'),'fecha':'12 Jun','hora':'21:00'},
            {'jornada':'Jornada 1','eq1':('qa','Qatar'),'eq2':('ch','Suiza'),'fecha':'13 Jun','hora':'21:00'},
            {'jornada':'Jornada 2','eq1':('ch','Suiza'),'eq2':('ba','Bosnia y Herzegovina'),'fecha':'18 Jun','hora':'21:00'},
            {'jornada':'Jornada 2','eq1':('ca','Canadá'),'eq2':('qa','Qatar'),'fecha':'19 Jun','hora':'00:00'},
            {'jornada':'Jornada 3','eq1':('ba','Bosnia y Herzegovina'),'eq2':('qa','Qatar'),'fecha':'24 Jun','hora':'21:00'},
            {'jornada':'Jornada 3','eq1':('ch','Suiza'),'eq2':('ca','Canadá'),'fecha':'24 Jun','hora':'21:00'},
        ],
        'C': [
            {'jornada':'Jornada 1','eq1':('br','Brasil'),'eq2':('ma','Marruecos'),'fecha':'14 Jun','hora':'00:00'},
            {'jornada':'Jornada 1','eq1':('ht','Haití'),'eq2':('gb-sct','Escocia'),'fecha':'14 Jun','hora':'03:00'},
            {'jornada':'Jornada 2','eq1':('gb-sct','Escocia'),'eq2':('ma','Marruecos'),'fecha':'20 Jun','hora':'00:00'},
            {'jornada':'Jornada 2','eq1':('br','Brasil'),'eq2':('ht','Haití'),'fecha':'20 Jun','hora':'02:30'},
            {'jornada':'Jornada 3','eq1':('gb-sct','Escocia'),'eq2':('br','Brasil'),'fecha':'25 Jun','hora':'00:00'},
            {'jornada':'Jornada 3','eq1':('ma','Marruecos'),'eq2':('ht','Haití'),'fecha':'25 Jun','hora':'00:00'},
        ],
        'D': [
            {'jornada':'Jornada 1','eq1':('us','Estados Unidos'),'eq2':('py','Paraguay'),'fecha':'13 Jun','hora':'03:00'},
            {'jornada':'Jornada 1','eq1':('au','Australia'),'eq2':('tr','Turquía'),'fecha':'14 Jun','hora':'06:00'},
            {'jornada':'Jornada 2','eq1':('us','Estados Unidos'),'eq2':('au','Australia'),'fecha':'19 Jun','hora':'21:00'},
            {'jornada':'Jornada 2','eq1':('tr','Turquía'),'eq2':('py','Paraguay'),'fecha':'20 Jun','hora':'05:00'},
            {'jornada':'Jornada 3','eq1':('tr','Turquía'),'eq2':('us','Estados Unidos'),'fecha':'26 Jun','hora':'04:00'},
            {'jornada':'Jornada 3','eq1':('py','Paraguay'),'eq2':('au','Australia'),'fecha':'26 Jun','hora':'04:00'},
        ],
        'E': [
            {'jornada':'Jornada 1','eq1':('de','Alemania'),'eq2':('cw','Curazao'),'fecha':'14 Jun','hora':'19:00'},
            {'jornada':'Jornada 1','eq1':('ci','Costa de Marfil'),'eq2':('ec','Ecuador'),'fecha':'15 Jun','hora':'01:00'},
            {'jornada':'Jornada 2','eq1':('de','Alemania'),'eq2':('ci','Costa de Marfil'),'fecha':'20 Jun','hora':'22:00'},
            {'jornada':'Jornada 2','eq1':('ec','Ecuador'),'eq2':('cw','Curazao'),'fecha':'21 Jun','hora':'02:00'},
            {'jornada':'Jornada 3','eq1':('ec','Ecuador'),'eq2':('de','Alemania'),'fecha':'25 Jun','hora':'22:00'},
            {'jornada':'Jornada 3','eq1':('cw','Curazao'),'eq2':('ci','Costa de Marfil'),'fecha':'25 Jun','hora':'22:00'},
        ],
        'F': [
            {'jornada':'Jornada 1','eq1':('nl','Países Bajos'),'eq2':('jp','Japón'),'fecha':'14 Jun','hora':'22:00'},
            {'jornada':'Jornada 1','eq1':('se','Suecia'),'eq2':('tn','Túnez'),'fecha':'15 Jun','hora':'04:00'},
            {'jornada':'Jornada 2','eq1':('nl','Países Bajos'),'eq2':('se','Suecia'),'fecha':'20 Jun','hora':'19:00'},
            {'jornada':'Jornada 2','eq1':('tn','Túnez'),'eq2':('jp','Japón'),'fecha':'21 Jun','hora':'06:00'},
            {'jornada':'Jornada 3','eq1':('jp','Japón'),'eq2':('se','Suecia'),'fecha':'26 Jun','hora':'01:00'},
            {'jornada':'Jornada 3','eq1':('tn','Túnez'),'eq2':('nl','Países Bajos'),'fecha':'26 Jun','hora':'01:00'},
        ],
        'G': [
            {'jornada':'Jornada 1','eq1':('be','Bélgica'),'eq2':('eg','Egipto'),'fecha':'15 Jun','hora':'21:00'},
            {'jornada':'Jornada 1','eq1':('ir','Irán'),'eq2':('nz','Nueva Zelanda'),'fecha':'16 Jun','hora':'03:00'},
            {'jornada':'Jornada 2','eq1':('be','Bélgica'),'eq2':('ir','Irán'),'fecha':'21 Jun','hora':'21:00'},
            {'jornada':'Jornada 2','eq1':('nz','Nueva Zelanda'),'eq2':('eg','Egipto'),'fecha':'22 Jun','hora':'03:00'},
            {'jornada':'Jornada 3','eq1':('nz','Nueva Zelanda'),'eq2':('be','Bélgica'),'fecha':'27 Jun','hora':'05:00'},
            {'jornada':'Jornada 3','eq1':('eg','Egipto'),'eq2':('ir','Irán'),'fecha':'27 Jun','hora':'05:00'},
        ],
        'H': [
            {'jornada':'Jornada 1','eq1':('es','España'),'eq2':('cv','Cabo Verde'),'fecha':'15 Jun','hora':'18:00'},
            {'jornada':'Jornada 1','eq1':('sa','Arabia Saudita'),'eq2':('uy','Uruguay'),'fecha':'16 Jun','hora':'00:00'},
            {'jornada':'Jornada 2','eq1':('es','España'),'eq2':('sa','Arabia Saudita'),'fecha':'21 Jun','hora':'18:00'},
            {'jornada':'Jornada 2','eq1':('uy','Uruguay'),'eq2':('cv','Cabo Verde'),'fecha':'22 Jun','hora':'00:00'},
            {'jornada':'Jornada 3','eq1':('uy','Uruguay'),'eq2':('es','España'),'fecha':'27 Jun','hora':'02:00'},
            {'jornada':'Jornada 3','eq1':('cv','Cabo Verde'),'eq2':('sa','Arabia Saudita'),'fecha':'27 Jun','hora':'02:00'},
        ],
        'I': [
            {'jornada':'Jornada 1','eq1':('fr','Francia'),'eq2':('sn','Senegal'),'fecha':'16 Jun','hora':'21:00'},
            {'jornada':'Jornada 1','eq1':('iq','Irak'),'eq2':('no','Noruega'),'fecha':'17 Jun','hora':'00:00'},
            {'jornada':'Jornada 2','eq1':('fr','Francia'),'eq2':('iq','Irak'),'fecha':'22 Jun','hora':'23:00'},
            {'jornada':'Jornada 2','eq1':('no','Noruega'),'eq2':('sn','Senegal'),'fecha':'23 Jun','hora':'02:00'},
            {'jornada':'Jornada 3','eq1':('sn','Senegal'),'eq2':('iq','Irak'),'fecha':'26 Jun','hora':'21:00'},
            {'jornada':'Jornada 3','eq1':('no','Noruega'),'eq2':('fr','Francia'),'fecha':'26 Jun','hora':'21:00'},
        ],
        'J': [
            {'jornada':'Jornada 1','eq1':('ar','Argentina'),'eq2':('dz','Argelia'),'fecha':'17 Jun','hora':'03:00'},
            {'jornada':'Jornada 1','eq1':('at','Austria'),'eq2':('jo','Jordania'),'fecha':'17 Jun','hora':'06:00'},
            {'jornada':'Jornada 2','eq1':('ar','Argentina'),'eq2':('at','Austria'),'fecha':'22 Jun','hora':'19:00'},
            {'jornada':'Jornada 2','eq1':('jo','Jordania'),'eq2':('dz','Argelia'),'fecha':'23 Jun','hora':'05:00'},
            {'jornada':'Jornada 3','eq1':('jo','Jordania'),'eq2':('ar','Argentina'),'fecha':'28 Jun','hora':'04:00'},
            {'jornada':'Jornada 3','eq1':('dz','Argelia'),'eq2':('at','Austria'),'fecha':'28 Jun','hora':'04:00'},
        ],
        'K': [
            {'jornada':'Jornada 1','eq1':('pt','Portugal'),'eq2':('cd','RD Congo'),'fecha':'17 Jun','hora':'19:00'},
            {'jornada':'Jornada 1','eq1':('uz','Uzbekistán'),'eq2':('co','Colombia'),'fecha':'18 Jun','hora':'04:00'},
            {'jornada':'Jornada 2','eq1':('pt','Portugal'),'eq2':('uz','Uzbekistán'),'fecha':'23 Jun','hora':'19:00'},
            {'jornada':'Jornada 2','eq1':('co','Colombia'),'eq2':('cd','RD Congo'),'fecha':'24 Jun','hora':'04:00'},
            {'jornada':'Jornada 3','eq1':('co','Colombia'),'eq2':('pt','Portugal'),'fecha':'28 Jun','hora':'01:30'},
            {'jornada':'Jornada 3','eq1':('cd','RD Congo'),'eq2':('uz','Uzbekistán'),'fecha':'28 Jun','hora':'01:30'},
        ],
        'L': [
            {'jornada':'Jornada 1','eq1':('gb-eng','Inglaterra'),'eq2':('hr','Croacia'),'fecha':'17 Jun','hora':'22:00'},
            {'jornada':'Jornada 1','eq1':('gh','Ghana'),'eq2':('pa','Panamá'),'fecha':'18 Jun','hora':'01:00'},
            {'jornada':'Jornada 2','eq1':('gb-eng','Inglaterra'),'eq2':('gh','Ghana'),'fecha':'23 Jun','hora':'22:00'},
            {'jornada':'Jornada 2','eq1':('pa','Panamá'),'eq2':('hr','Croacia'),'fecha':'24 Jun','hora':'01:00'},
            {'jornada':'Jornada 3','eq1':('hr','Croacia'),'eq2':('gh','Ghana'),'fecha':'27 Jun','hora':'23:00'},
            {'jornada':'Jornada 3','eq1':('pa','Panamá'),'eq2':('gb-eng','Inglaterra'),'fecha':'27 Jun','hora':'23:00'},
        ],
    }


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@public_bp.route("/")
def welcome():
    if not _logged_in():
        return _render("login_register")
    return _render_ranking()


SHARED_USERNAME = "Elecnor"
SHARED_PASSWORD = "Mundial26"


def _authenticated():
    return session.get("authenticated", False)

def _require_auth():
    return redirect(url_for("public.welcome"))


@public_bp.post("/entrar")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if username.lower() != SHARED_USERNAME.lower() or password != SHARED_PASSWORD:
        return _render("login_register", auth_error="Usuario o contraseña incorrectos.")
    session["authenticated"] = True
    return redirect(url_for("public.welcome"))


@public_bp.post("/registro")
def register():
    return redirect(url_for("public.welcome"))


@public_bp.route("/salir")
def logout():
    session.clear()
    return redirect(url_for("public.welcome"))


@public_bp.route("/nueva-prediccion", methods=["GET", "POST"])
def nueva_prediccion():
    if not _logged_in():
        return redirect(url_for("public.welcome"))
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            return _render("nuevo_nombre", nombre_error="Introduce tu nombre.")
        session["pred_nombre"] = nombre
        return redirect(url_for("public.grupos_fase"))
    return _render("nuevo_nombre")


def _auto_sync():
    """Sync from API at most once per minute (API free tier: 10 req/min, sync uses 2)."""
    from flask import current_app
    import datetime
    api_key = current_app.config.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        return
    try:
        storage = get_storage()
        now_utc = datetime.datetime.utcnow()
        last_sync_str = storage.get_setting("last_sync", "")
        if last_sync_str:
            elapsed = (now_utc - datetime.datetime.fromisoformat(last_sync_str)).total_seconds()
            if elapsed < 15:
                return  # Already synced less than 15 seconds ago
        from app.services.sync import fetch_all
        data = fetch_all(api_key)
        new_results = data.get("results", {})
        if new_results:
            existing = storage.load_results()
            existing.update(new_results)
            storage.save_results(existing)
        fixtures = data.get("fixtures", [])
        if fixtures:
            storage.save_fixtures(fixtures)
        storage.set_setting("last_sync", now_utc.isoformat())
    except Exception:
        pass


def _render_ranking():
    _auto_sync()
    try:
        storage = get_storage()
        participants = storage.load_participants()
        results = storage.load_results()
    except Exception:
        participants, results = {}, {}
    standings = build_standings(participants, results)
    try:
        all_p = get_storage().load_participants_full()
        id_map = {p["name"]: p["id"] for p in all_p}
        for row in standings:
            row["id"] = id_map.get(row["name"], "")
    except Exception:
        for row in standings:
            row["id"] = ""
    return _render("inicio", clasificacion=standings)


@public_bp.route("/ranking")
def ranking():
    return _render_ranking()


_KNOCKOUT_STAGES = {"ROUND_OF_32","LAST_32","ROUND_OF_16","LAST_16","QUARTER_FINALS","SEMI_FINALS","FINAL","THIRD_PLACE"}
_KNOCKOUT_ORDER  = ["ROUND_OF_32","LAST_32","ROUND_OF_16","LAST_16","QUARTER_FINALS","SEMI_FINALS","FINAL"]
_KNOCKOUT_LABELS = {
    "ROUND_OF_32":    "Dieciseisavos de Final",
    "LAST_32":        "Dieciseisavos de Final",
    "ROUND_OF_16":    "Octavos de Final",
    "LAST_16":        "Octavos de Final",
    "QUARTER_FINALS": "Cuartos de Final",
    "SEMI_FINALS":    "Semifinales",
    "FINAL":          "Final",
    "THIRD_PLACE":    "3er y 4º Puesto",
}


@public_bp.route("/grupos")
def ver_grupos():
    try:
        storage  = get_storage()
        results  = storage.load_results()
        fixtures = storage.load_fixtures()
    except Exception:
        results, fixtures = {}, []

    # Only switch to knockout view when at least one knockout match has been played or is live
    knockout_fixtures = [f for f in fixtures if f.get("stage","") in _KNOCKOUT_STAGES]
    in_knockout = any(f.get("is_finished") or f.get("is_live") for f in knockout_fixtures)

    if in_knockout:
        # Group knockout fixtures by stage in order
        from collections import OrderedDict
        rondas = OrderedDict()
        seen_stages = set()
        for stage in _KNOCKOUT_ORDER + ["THIRD_PLACE"]:
            matches = [f for f in knockout_fixtures if f.get("stage") == stage]
            if matches and stage not in seen_stages:
                seen_stages.add(stage)
                rondas[_KNOCKOUT_LABELS[stage]] = matches
        return _render("ver_eliminatorias", rondas=rondas)

    # Group stage view
    grupos_fmt = _grupos_fmt()
    grupos_ordenados = {}
    for letra, equipos in grupos_fmt.items():
        letra_min = letra.lower()
        r1 = results.get(f"g_{letra_min}_1", "")
        r2 = results.get(f"g_{letra_min}_2", "")
        r3 = results.get(f"g_{letra_min}_3", "")
        equipos_dict = {pais: iso for iso, pais in equipos}
        ordenados = []
        if r1 in equipos_dict: ordenados.append((equipos_dict[r1], r1, "1º"))
        if r2 in equipos_dict: ordenados.append((equipos_dict[r2], r2, "2º"))
        if r3 in equipos_dict: ordenados.append((equipos_dict[r3], r3, "3º"))
        puestos = [e[1] for e in ordenados]
        for iso, pais in equipos:
            if pais not in puestos:
                ordenados.append((iso, pais, "-"))
        grupos_ordenados[letra] = ordenados
    return _render("ver_grupos", grupos_ordenados=grupos_ordenados)


@public_bp.route("/horarios")
def ver_horarios():
    # Try dynamic fixtures from DB first
    fixtures = []
    try:
        fixtures = get_storage().load_fixtures()
    except Exception:
        pass

    if fixtures:
        # Group fixtures by stage/group for display
        from collections import OrderedDict
        sections = OrderedDict()  # key → {"label": str, "partidos": [...]}

        stage_order = [
            "GROUP_STAGE", "ROUND_OF_32", "LAST_32",
            "ROUND_OF_16", "LAST_16", "QUARTER_FINALS",
            "SEMI_FINALS", "THIRD_PLACE", "FINAL",
        ]
        # Sort fixtures by date within each group
        def _sort_key(f):
            stage_idx = stage_order.index(f["stage"]) if f["stage"] in stage_order else 99
            return (stage_idx, f.get("group", ""), f.get("fecha", ""), f.get("hora", ""))

        fixtures_sorted = sorted(fixtures, key=_sort_key)

        for f in fixtures_sorted:
            stage = f["stage"]
            group = f.get("group", "")
            if stage == "GROUP_STAGE":
                sec_key = f"grupo_{group}"
                label   = f"Grupo {group}"
            else:
                sec_key = stage
                label   = f["stage_label"]
            if sec_key not in sections:
                sections[sec_key] = {"label": label, "partidos": []}
            sections[sec_key]["partidos"].append(f)

        return _render("ver_horarios_dinamico", sections=sections)

    # Fallback to hardcoded calendar
    return _render("ver_horarios", calendario=_generar_calendario())


@public_bp.route("/prediccion/ver/<participant_id>")
def ver_prediccion(participant_id):
    if not _logged_in():
        return redirect(url_for("public.welcome"))
    try:
        p = get_storage().get_participant_by_id(participant_id)
    except Exception:
        return redirect(url_for("public.welcome"))
    if not p:
        return redirect(url_for("public.welcome"))
    return _render("ver_prediccion", nombre=p["name"], predicciones=p.get("prediction") or {})


@public_bp.route("/prediccion/grupos", methods=["GET", "POST"])
def grupos_fase():
    if not _logged_in():
        return redirect(url_for("public.welcome"))
    nombre = session.get("pred_nombre", "")
    if not nombre:
        return redirect(url_for("public.nueva_prediccion"))
    if request.method == "POST":
        pred = {"grupos": request.form.to_dict(), "eliminatorias": {}}
        session["pred_grupos"] = request.form.to_dict()
        try:
            get_storage().save_prediction_by_name(nombre, pred)
        except Exception:
            pass
        return redirect(url_for("public.eliminatorias_fase"))
    saved = session.get("pred_grupos", {})
    if not saved:
        try:
            p = get_storage().get_prediction_by_name(nombre)
            if p:
                saved = p.get("prediction", {}).get("grupos", {})
        except Exception:
            pass
    return _render("fase_grupos", grupos=_grupos_fmt(), saved=saved)


@public_bp.route("/prediccion/eliminatorias", methods=["GET", "POST"])
def eliminatorias_fase():
    if not _logged_in():
        return redirect(url_for("public.welcome"))
    nombre = session.get("pred_nombre", "")
    if not nombre:
        return redirect(url_for("public.nueva_prediccion"))
    if request.method == "POST":
        elim = {
            "octavos": request.form.getlist("octavos"),
            "cuartos": request.form.getlist("cuartos"),
            "semis": request.form.getlist("semis"),
            "final": request.form.getlist("final"),
            "campeon": request.form.get("campeon"),
            "subcampeon": request.form.get("subcampeon"),
            "pichichi": request.form.get("pichichi"),
        }
        try:
            storage = get_storage()
            p = storage.get_prediction_by_name(nombre)
            pred = p.get("prediction", {}) if p else {"grupos": {}}
            pred["eliminatorias"] = elim
            storage.save_prediction_by_name(nombre, pred)
        except Exception:
            pass
        session.pop("pred_nombre", None)
        session.pop("pred_grupos", None)
        return redirect(url_for("public.welcome"))
    grupos_data = session.get("pred_grupos", {})
    if not grupos_data:
        return redirect(url_for("public.grupos_fase"))
    clasificados = []
    seen = set()
    for letra in "ABCDEFGHIJKL":
        for pos in ("1", "2", "3"):
            eq = grupos_data.get(f"g_{letra}_{pos}", "")
            if eq and eq not in seen:
                clasificados.append(eq)
                seen.add(eq)
    if not clasificados:
        return redirect(url_for("public.grupos_fase"))
    return _render("eliminatorias", nombre=nombre, clasificados=clasificados)


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------
@public_bp.route("/admin", methods=["GET", "POST"])
def admin():
    from flask import current_app

    # Admin is accessible to anyone logged in with Elecnor/Mundial26
    authed = session.get("authenticated", False)
    if not authed:
        return redirect(url_for("public.welcome"))

    msg, ok, error = None, False, None

    if request.method == "POST":
        action = request.form.get("action")
        if False:  # placeholder to keep elif chain
            pass

        elif action == "sync_api" and authed:
            api_key = current_app.config.get("FOOTBALL_DATA_API_KEY", "")
            if not api_key:
                msg, ok = "Falta FOOTBALL_DATA_API_KEY en las variables de entorno de Vercel.", False
            else:
                try:
                    from app.services.sync import fetch_all
                    data = fetch_all(api_key)
                    storage = get_storage()
                    new_results = data.get("results", {})
                    if new_results:
                        existing = storage.load_results()
                        existing.update(new_results)
                        storage.save_results(existing)
                    fixtures = data.get("fixtures", [])
                    if fixtures:
                        storage.save_fixtures(fixtures)
                    msg, ok = f"Sincronizado: {len(new_results)} resultados, {len(fixtures)} partidos.", True
                except Exception as exc:
                    msg, ok = f"Error al sincronizar: {exc}", False

        elif action == "save_results" and authed:
            try:
                results = {}
                for letra in "ABCDEFGHIJKL":
                    for pos in ("1", "2", "3"):
                        val = request.form.get(f"g_{letra}_{pos}", "").strip()
                        if val:
                            results[f"g_{letra.lower()}_{pos}"] = val
                for ronda in ("octavos", "cuartos", "semis", "final"):
                    vals = request.form.getlist(ronda)
                    if vals:
                        results[ronda] = vals
                for field in ("campeon", "subcampeon"):
                    val = request.form.get(field, "").strip()
                    if val:
                        results[field] = val
                pichichi = request.form.get("pichichi", "").strip()
                if pichichi:
                    results["pichichi"] = [pichichi.lower()]
                get_storage().save_results(results)
                msg, ok = "Resultados guardados correctamente.", True
            except Exception as exc:
                msg, ok = f"Error al guardar: {exc}", False

    current_results = {}
    if authed:
        try:
            current_results = get_storage().load_results()
        except Exception:
            pass

    grupos_fmt = _grupos_fmt()
    all_teams = sorted(set(pais for equipos in grupos_fmt.values() for _, pais in equipos))

    from flask import current_app as _app
    has_api_key = bool(_app.config.get("FOOTBALL_DATA_API_KEY", ""))

    # Render admin with Bootstrap (same style as the rest of the app)
    ADMIN_HTML = """
<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin – Porra Mundial 2026</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
  body{font-family:'Poppins',sans-serif;background:#f2f9f5;color:#2c3e50;padding-top:30px;}
  .card{border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.05);border:none;background:rgba(255,255,255,.98);}
  .team-checkbox{display:none;}
  .team-label{cursor:pointer;border:2px solid #dee2e6;border-radius:8px;padding:8px;transition:all .2s;display:block;text-align:center;background:white;font-weight:600;font-size:.85rem;}
  .team-checkbox:checked+.team-label{border-color:#198754;background:#e8f5e9;color:#0f5132;}
</style>
</head><body>
<div class="container-fluid px-4 mb-5" style="max-width:1300px;">
  <div class="d-flex justify-content-between align-items-center py-3 mb-4 border-bottom border-success">
    <h2 class="fw-bold text-success m-0">⚙️ Panel de Administrador</h2>
    <a href="/" class="btn btn-outline-success fw-bold">← Volver a la app</a>
  </div>

  {% if not authed %}
  <div class="row justify-content-center"><div class="col-md-4">
    <div class="card p-4">
      <h4 class="fw-bold text-success border-bottom pb-3 mb-4 text-center">Acceso Admin</h4>
      {% if error %}<div class="alert alert-danger py-2">{{ error }}</div>{% endif %}
      <form method="POST">
        <input type="hidden" name="action" value="login">
        <div class="mb-3"><label class="form-label fw-bold text-success">Contraseña</label>
        <input type="password" name="admin_password" class="form-control border-success" required></div>
        <button type="submit" class="btn btn-success fw-bold w-100 py-2">Entrar</button>
      </form>
    </div>
  </div></div>

  {% else %}
  {% if msg %}<div class="alert {{ 'alert-success' if ok else 'alert-danger' }} fw-bold">{{ msg }}</div>{% endif %}

  <div class="card p-3 mb-4">
    <h5 class="fw-bold text-success mb-3">🔄 Sincronización Automática</h5>
    <form method="POST" class="d-flex gap-3 align-items-center flex-wrap">
      <input type="hidden" name="action" value="sync_api">
      <button type="submit" class="btn btn-primary fw-bold" {{ '' if has_api_key else 'disabled' }}>
        🔄 Sincronizar desde API del Mundial
      </button>
      {% if not has_api_key %}
      <span class="text-danger fw-bold small">⚠️ Falta configurar FOOTBALL_DATA_API_KEY en Vercel</span>
      {% else %}
      <span class="text-muted small">Actualiza automáticamente con resultados reales de football-data.org</span>
      {% endif %}
    </form>
  </div>

  <form method="POST">
    <input type="hidden" name="action" value="save_results">

    <div class="card p-3 mb-4">
      <h5 class="fw-bold text-success mb-3">🌍 Fase de Grupos</h5>
      <div class="row">
        {% for letra, equipos in grupos.items() %}
        <div class="col-md-6 col-lg-3 mb-3">
          <div class="card bg-light border-0 shadow-sm h-100">
            <div class="card-header bg-success text-white fw-bold text-center py-2">Grupo {{ letra }}</div>
            <div class="card-body p-3 d-flex flex-column gap-2">
              {% for pos, label in [('1','1º Puesto'),('2','2º Puesto'),('3','Mejor 3º')] %}
              <select name="g_{{ letra }}_{{ pos }}" class="form-select form-select-sm fw-bold">
                <option value="">{{ label }} — sin resultado</option>
                {% for iso, pais in equipos %}
                <option value="{{ pais }}" {{ 'selected' if results.get('g_' ~ letra.lower() ~ '_' ~ pos) == pais }}>
                  {{ label }} · {{ pais }}
                </option>
                {% endfor %}
              </select>
              {% endfor %}
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>

    <div class="card p-3 mb-4">
      <h5 class="fw-bold text-success mb-3">⚽ Eliminatorias</h5>
      {% for ronda, label, maxsel in [('octavos','Octavos de Final',16),('cuartos','Cuartos de Final',8),('semis','Semifinales',4),('final','Final',2)] %}
      <h6 class="fw-bold text-dark mt-3 mb-2">{{ label }} ({{ maxsel }} equipos)</h6>
      <div class="row g-2 mb-3">
        {% for tname in all_teams %}
        <div class="col-6 col-md-3 col-lg-2">
          <input type="checkbox" name="{{ ronda }}" value="{{ tname }}" id="r_{{ ronda }}_{{ loop.index }}" class="team-checkbox"
                 {{ 'checked' if tname in (results.get(ronda) or []) }}>
          <label class="team-label" for="r_{{ ronda }}_{{ loop.index }}">{{ tname }}</label>
        </div>
        {% endfor %}
      </div>
      {% endfor %}

      <div class="row mt-3">
        <div class="col-md-4 mb-3">
          <label class="form-label fw-bold text-success">🏆 Campeón</label>
          <select name="campeon" class="form-select fw-bold">
            <option value="">— sin resultado —</option>
            {% for tname in all_teams %}
            <option value="{{ tname }}" {{ 'selected' if results.get('campeon') == tname }}>{{ tname }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-md-4 mb-3">
          <label class="form-label fw-bold text-secondary">🥈 Subcampeón</label>
          <select name="subcampeon" class="form-select fw-bold">
            <option value="">— sin resultado —</option>
            {% for tname in all_teams %}
            <option value="{{ tname }}" {{ 'selected' if results.get('subcampeon') == tname }}>{{ tname }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-md-4 mb-3">
          <label class="form-label fw-bold text-primary">⚽ Pichichi</label>
          <input type="text" name="pichichi" class="form-control fw-bold"
                 value="{{ results.get('pichichi',[''])[0] if results.get('pichichi') else '' }}"
                 placeholder="Ej: Kylian Mbappé">
        </div>
      </div>
    </div>

    <div class="text-center mb-5">
      <button type="submit" class="btn btn-success fw-bold px-5 py-3 fs-5">💾 Guardar resultados</button>
    </div>
  </form>
  {% endif %}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body></html>
"""
    return render_template_string(
        ADMIN_HTML,
        authed=True, grupos=grupos_fmt, all_teams=all_teams,
        results=current_results, msg=msg, ok=ok, error=error,
        has_api_key=has_api_key,
    )


@public_bp.route("/sync")
def sync_results():
    from flask import current_app
    from app.services.sync import fetch_all
    secret = current_app.config.get("SYNC_SECRET", "")
    if secret and request.args.get("secret") != secret:
        return {"error": "unauthorized"}, 401
    api_key = current_app.config.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        return {"error": "FOOTBALL_DATA_API_KEY not configured"}, 500
    try:
        data = fetch_all(api_key)
        storage = get_storage()
        # Save results (merge with existing manual entries)
        new_results = data.get("results", {})
        if new_results:
            existing = storage.load_results()
            existing.update(new_results)
            storage.save_results(existing)
        # Save fixtures (full replace)
        fixtures = data.get("fixtures", [])
        if fixtures:
            storage.save_fixtures(fixtures)
        return {
            "status": "ok",
            "results_keys": list(new_results.keys()),
            "fixtures_count": len(fixtures),
        }
    except Exception as exc:
        return {"error": str(exc)}, 500


@public_bp.route("/health")
def health():
    return {"status": "ok"}
