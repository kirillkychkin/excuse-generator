def test_stats(client):
    for delay in (5, 15):
        client.post(
            "/api/excuses/generate",
            json={"username": "kirill", "subject": "Философия", "delay_minutes": delay},
        )
    history = client.get("/api/users/kirill/history").json()
    client.post(f"/api/history/{history[0]['id']}/feedback", json={"worked": True})
    client.post(f"/api/history/{history[1]['id']}/feedback", json={"worked": False})

    response = client.get("/api/users/kirill/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total"] == 2
    assert stats["last_week"] == 2
    assert stats["average_delay"] == 10.0
    assert stats["success_rate"] == 0.5
    assert stats["favorite_theme"] in {h["theme"] for h in history}


def test_stats_of_unknown_user(client):
    assert client.get("/api/users/nobody/stats").status_code == 404
