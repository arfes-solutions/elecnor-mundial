from flask import Blueprint, redirect, render_template, request, url_for

from app.data.tournament import GROUPS, TEAMS
from app.services.scoring import build_standings
from app.storage import get_storage


public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def welcome():
    return render_template("public/welcome.html")


@public_bp.post("/entrar")
def login():
    name = request.form.get("name", "").strip()
    if not name:
        return render_template("public/welcome.html", login_error="Introduce tu nombre.")

    participants = get_storage().load_participants()
    if name not in participants:
        return render_template(
            "public/welcome.html",
            login_error="No encontramos ese participante. Puedes registrarlo ahora.",
            suggested_name=name,
        )

    return redirect(url_for("public.ranking"))


@public_bp.post("/registro")
def register():
    name = request.form.get("name", "").strip()
    if not name:
        return render_template("public/welcome.html", register_error="Introduce tu nombre.")

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

    return render_template(
        "public/dashboard.html",
        groups=GROUPS,
        teams=TEAMS,
        participants=participants,
        results=results,
        standings=standings,
    )


@public_bp.route("/health")
def health():
    return {"status": "ok"}
