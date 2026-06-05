from flask import current_app


def get_client():
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("Supabase storage requires the 'supabase' package.") from exc

    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")

    return create_client(url, key)


def load_participants():
    response = (
        get_client()
        .table("participants")
        .select("name,prediction_json")
        .order("created_at")
        .execute()
    )
    return {row["name"]: row.get("prediction_json") or {} for row in response.data}


def save_participant(name, prediction):
    get_client().table("participants").upsert(
        {"name": name.strip(), "prediction_json": prediction},
        on_conflict="name",
    ).execute()


def load_results():
    response = (
        get_client()
        .table("results")
        .select("results_json")
        .eq("id", 1)
        .limit(1)
        .execute()
    )
    if not response.data:
        return {}
    return response.data[0].get("results_json") or {}


def save_results(results):
    get_client().table("results").upsert(
        {"id": 1, "results_json": results},
        on_conflict="id",
    ).execute()


def get_setting(key, default=None):
    response = (
        get_client()
        .table("settings")
        .select("value")
        .eq("key", key)
        .limit(1)
        .execute()
    )
    if not response.data:
        return default
    return response.data[0]["value"]


def set_setting(key, value):
    get_client().table("settings").upsert(
        {"key": key, "value": value},
        on_conflict="key",
    ).execute()
