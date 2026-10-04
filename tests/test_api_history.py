REQUEST = {"username": "kirill", "subject": "Физика", "delay_minutes": 7}


def generate(client):
    return client.post("/api/excuses/generate", json=REQUEST).json()


def test_history_lists_generated_excuses(client):
    first = generate(client)
    second = generate(client)

    response = client.get("/api/users/kirill/history")

    assert response.status_code == 200
    history = response.json()
    assert [h["id"] for h in history] == [second["history_id"], first["history_id"]]
    assert history[0]["text"] == second["text"]
    assert history[0]["subject"] == "Физика"
    assert history[0]["worked"] is None


def test_history_of_unknown_user(client):
    assert client.get("/api/users/nobody/history").status_code == 404


def test_feedback_updates_history(client):
    excuse = generate(client)

    response = client.post(f"/api/history/{excuse['history_id']}/feedback", json={"worked": False})

    assert response.status_code == 200
    assert response.json()["worked"] is False
    assert client.get("/api/users/kirill/history").json()[0]["worked"] is False


def test_feedback_for_unknown_item(client):
    response = client.post("/api/history/999/feedback", json={"worked": True})

    assert response.status_code == 404
