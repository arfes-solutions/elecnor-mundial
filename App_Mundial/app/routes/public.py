from flask import Blueprint, render_template

from app.data.tournament import GROUPS, TEAMS
from app.services.scoring import build_standings
from app.storage import get_storage


public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def dashboard():
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
