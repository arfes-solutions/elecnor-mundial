"""
Sync real World Cup 2026 results from football-data.org API.
Competition code: WC  (FIFA World Cup)
Docs: https://docs.football-data.org/general/v4/index.html
"""
import requests as _req

_BASE = "https://api.football-data.org/v4"
_COMPETITION = "WC"

# Map API team names → our internal names (tournament.py TEAMS)
_NAME_MAP = {
    "Mexico": "México",
    "South Africa": "Sudáfrica",
    "Korea Republic": "Corea del Sur",
    "Czech Republic": "Chequia",
    "Czechia": "Chequia",
    "Canada": "Canadá",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "Qatar": "Qatar",
    "Switzerland": "Suiza",
    "Brazil": "Brasil",
    "Morocco": "Marruecos",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    "United States": "Estados Unidos",
    "USA": "Estados Unidos",
    "Paraguay": "Paraguay",
    "Australia": "Australia",
    "Türkiye": "Turquía",
    "Turkey": "Turquía",
    "Germany": "Alemania",
    "Curaçao": "Curazao",
    "Ivory Coast": "Costa de Marfil",
    "Côte d'Ivoire": "Costa de Marfil",
    "Ecuador": "Ecuador",
    "Netherlands": "Países Bajos",
    "Japan": "Japón",
    "Sweden": "Suecia",
    "Tunisia": "Túnez",
    "Belgium": "Bélgica",
    "Egypt": "Egipto",
    "Iran": "Irán",
    "New Zealand": "Nueva Zelanda",
    "Spain": "España",
    "Cape Verde": "Cabo Verde",
    "Saudi Arabia": "Arabia Saudita",
    "Uruguay": "Uruguay",
    "France": "Francia",
    "Senegal": "Senegal",
    "Iraq": "Irak",
    "Norway": "Noruega",
    "Argentina": "Argentina",
    "Algeria": "Argelia",
    "Austria": "Austria",
    "Jordan": "Jordania",
    "Portugal": "Portugal",
    "DR Congo": "RD Congo",
    "Uzbekistan": "Uzbekistán",
    "Colombia": "Colombia",
    "England": "Inglaterra",
    "Croatia": "Croacia",
    "Ghana": "Ghana",
    "Panama": "Panamá",
}

# Map knockout stage names from API → our keys
_STAGE_MAP = {
    "ROUND_OF_32": "octavos",
    "LAST_32": "octavos",
    "ROUND_OF_16": "cuartos",
    "LAST_16": "cuartos",
    "QUARTER_FINALS": "semis",
    "SEMI_FINALS": "final",
    "FINAL": None,  # handled separately for champion/runner-up
}


def _norm(name: str) -> str:
    return _NAME_MAP.get(name, name)


def _headers(api_key: str) -> dict:
    return {"X-Auth-Token": api_key}


def fetch_results(api_key: str) -> dict:
    """
    Fetch current WC 2026 results and return a dict in our results_json format.
    Returns empty dict on any error so existing results are preserved.
    """
    results = {}

    try:
        # --- GROUP STANDINGS ---
        r = _req.get(
            f"{_BASE}/competitions/{_COMPETITION}/standings",
            headers=_headers(api_key),
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            for standing in data.get("standings", []):
                if standing.get("type") != "TOTAL":
                    continue
                group_letter = standing.get("group", "").replace("GROUP_", "")
                if not group_letter or len(group_letter) != 1:
                    continue
                table = standing.get("table", [])
                for row in table:
                    pos = row.get("position")
                    team_name = _norm(row.get("team", {}).get("name", ""))
                    if pos in (1, 2, 3) and team_name:
                        results[f"g_{group_letter.lower()}_{pos}"] = team_name

        # --- KNOCKOUT MATCHES ---
        r = _req.get(
            f"{_BASE}/competitions/{_COMPETITION}/matches",
            headers=_headers(api_key),
            timeout=10,
        )
        if r.status_code == 200:
            matches = r.json().get("matches", [])
            advanced: dict[str, set] = {
                "octavos": set(),
                "cuartos": set(),
                "semis": set(),
                "final": set(),
            }
            champion = None
            runner_up = None

            for match in matches:
                stage = match.get("stage", "")
                our_round = _STAGE_MAP.get(stage)
                status = match.get("status", "")
                if status not in ("FINISHED",):
                    continue

                score = match.get("score", {})
                home_goals = (score.get("fullTime") or {}).get("home")
                away_goals = (score.get("fullTime") or {}).get("away")
                # include extra time / penalties
                if home_goals is None:
                    ft = score.get("regularTime") or {}
                    home_goals = ft.get("home")
                    away_goals = ft.get("away")

                home = _norm(match.get("homeTeam", {}).get("name", ""))
                away = _norm(match.get("awayTeam", {}).get("name", ""))

                if stage == "FINAL" and home_goals is not None:
                    # Determine winner via penalties if needed
                    winner_id = match.get("score", {}).get("winner")
                    if winner_id == "HOME_TEAM":
                        champion, runner_up = home, away
                    elif winner_id == "AWAY_TEAM":
                        champion, runner_up = away, home

                elif our_round and home_goals is not None:
                    winner_id = match.get("score", {}).get("winner")
                    if winner_id == "HOME_TEAM":
                        advanced[our_round].add(home)
                    elif winner_id == "AWAY_TEAM":
                        advanced[our_round].add(away)

            for ronda, teams in advanced.items():
                if teams:
                    results[ronda] = sorted(teams)

            if champion:
                results["campeon"] = champion
            if runner_up:
                results["subcampeon"] = runner_up

    except Exception:
        pass

    return results
