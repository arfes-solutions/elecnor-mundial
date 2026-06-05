import json

from app.db import get_db


def load_participants():
    rows = get_db().execute(
        "SELECT name, prediction_json FROM participants ORDER BY created_at ASC"
    ).fetchall()

    participants = {}
    for row in rows:
        participants[row["name"]] = json.loads(row["prediction_json"])
    return participants


def save_participant(name, prediction):
    payload = json.dumps(prediction, ensure_ascii=False)
    get_db().execute(
        """
        INSERT INTO participants (name, prediction_json)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET
            prediction_json = excluded.prediction_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (name.strip(), payload),
    )
    get_db().commit()


def load_results():
    row = get_db().execute(
        "SELECT results_json FROM results WHERE id = 1"
    ).fetchone()
    if row is None:
        return {}
    return json.loads(row["results_json"])


def save_results(results):
    payload = json.dumps(results, ensure_ascii=False)
    get_db().execute(
        """
        INSERT INTO results (id, results_json)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET
            results_json = excluded.results_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (payload,),
    )
    get_db().commit()


def get_setting(key, default=None):
    row = get_db().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return row["value"]


def set_setting(key, value):
    get_db().execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    get_db().commit()
