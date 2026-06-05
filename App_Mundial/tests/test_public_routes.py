from app.storage.sqlite import save_participant, save_results


def test_dashboard_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Porra Mundial" in response.text
    assert "Clasificación" in response.text


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_dashboard_reads_sqlite_participants(app, client):
    with app.app_context():
        save_participant(
            "Ibon",
            {
                "grupos": {"g_A_1": "México"},
                "eliminatorias": {"campeon": "España"},
            },
        )
        save_results({"g_a_1": "México", "campeon": "España"})

    response = client.get("/")

    assert response.status_code == 200
    assert "Ibon" in response.text
    assert "22 pts" in response.text
