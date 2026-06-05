import requests
from flask import current_app


def _headers():
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _url(path):
    base = current_app.config.get("SUPABASE_URL", "").rstrip("/")
    return f"{base}/rest/v1/{path}"


def _check(response):
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase error {response.status_code}: {response.text}")
    return response


def load_participants():
    r = _check(requests.get(
        _url("participants"),
        headers=_headers(),
        params={"select": "name,prediction_json", "order": "created_at"},
    ))
    return {row["name"]: row.get("prediction_json") or {} for row in r.json()}


def load_participants_full():
    r = _check(requests.get(
        _url("participants"),
        headers=_headers(),
        params={"select": "id,name,prediction_json", "order": "created_at"},
    ))
    return r.json()


def get_participant_by_id(participant_id):
    r = _check(requests.get(
        _url("participants"),
        headers=_headers(),
        params={
            "select": "id,name,email,password_hash,prediction_json",
            "id": f"eq.{participant_id}",
            "limit": "1",
        },
    ))
    data = r.json()
    if not data:
        return None
    row = data[0]
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row.get("email"),
        "password_hash": row.get("password_hash"),
        "prediction": row.get("prediction_json") or {},
    }


def update_prediction(participant_id, prediction):
    _check(requests.patch(
        _url("participants"),
        headers=_headers(),
        params={"id": f"eq.{participant_id}"},
        json={"prediction_json": prediction},
    ))


def get_participant_by_email(email):
    r = _check(requests.get(
        _url("participants"),
        headers=_headers(),
        params={
            "select": "id,name,email,password_hash,prediction_json",
            "email": f"ilike.{email.strip()}",
            "limit": "1",
        },
    ))
    data = r.json()
    if not data:
        return None
    row = data[0]
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row.get("email"),
        "password_hash": row.get("password_hash"),
        "prediction": row.get("prediction_json") or {},
    }


def get_participant_by_name(name):
    r = _check(requests.get(
        _url("participants"),
        headers=_headers(),
        params={
            "select": "id,name,email,password_hash,prediction_json",
            "name": f"ilike.{name.strip()}",
            "limit": "1",
        },
    ))
    data = r.json()
    if not data:
        return None
    row = data[0]
    return {
        "id": row["id"],
        "name": row["name"],
        "password_hash": row.get("password_hash"),
        "prediction": row.get("prediction_json") or {},
    }


def create_participant(name, email, password_hash):
    # email is kept for DB compatibility but can be a dummy value
    _check(requests.post(
        _url("participants"),
        headers=_headers(),
        json={
            "name": name.strip(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "prediction_json": {"grupos": {}, "eliminatorias": {}},
        },
    ))


def save_participant(name, prediction, email=None, password_hash=None):
    payload = {"name": name.strip(), "prediction_json": prediction}
    if email:
        payload["email"] = email.strip().lower()
    if password_hash:
        payload["password_hash"] = password_hash
    h = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
    _check(requests.post(_url("participants"), headers=h, json=payload))


def load_results():
    r = _check(requests.get(
        _url("results"),
        headers=_headers(),
        params={"select": "results_json", "id": "eq.1", "limit": "1"},
    ))
    data = r.json()
    if not data:
        return {}
    return data[0].get("results_json") or {}


def save_results(results):
    h = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
    _check(requests.post(_url("results"), headers=h, json={"id": 1, "results_json": results}))


def get_setting(key, default=None):
    r = _check(requests.get(
        _url("settings"),
        headers=_headers(),
        params={"select": "value", "key": f"eq.{key}", "limit": "1"},
    ))
    data = r.json()
    if not data:
        return default
    return data[0]["value"]


def set_setting(key, value):
    h = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
    _check(requests.post(_url("settings"), headers=h, json={"key": key, "value": value}))
