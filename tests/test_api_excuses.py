import pytest
from sqlalchemy import delete

from app.models import ExcuseTemplate

REQUEST = {
    "username": "kirill",
    "subject": "Программирование на Python",
    "delay_minutes": 12,
    "at": "2026-10-05T09:00:00",
}


def test_generate_excuse(client):
    response = client.post("/api/excuses/generate", json=REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["text"]
    assert body["delay_category"] == "medium"
    assert body["time_of_day"] == "morning"
    assert body["risk_level"] == "low"
    assert body["warning"] is None
    assert 1 <= body["credibility"] <= 5


def test_generate_creates_user(client):
    client.post("/api/excuses/generate", json=REQUEST)

    assert client.get("/api/users/kirill").status_code == 200


def test_generate_warns_frequent_latecomer(client):
    for _ in range(4):
        client.post("/api/excuses/generate", json=REQUEST)

    body = client.post("/api/excuses/generate", json=REQUEST).json()

    assert body["risk_level"] == "high"
    assert body["lateness_last_week"] == 4
    assert body["warning"]


def test_generate_unknown_subject(client):
    response = client.post("/api/excuses/generate", json={**REQUEST, "subject": "Астрология"})

    assert response.status_code == 404
    assert "Астрология" in response.json()["detail"]


@pytest.mark.parametrize("delay", [0, -5, 181])
def test_generate_validates_delay(client, delay):
    response = client.post("/api/excuses/generate", json={**REQUEST, "delay_minutes": delay})

    assert response.status_code == 422


def test_generate_without_templates(client, seeded_session):
    seeded_session.execute(delete(ExcuseTemplate))
    seeded_session.commit()

    response = client.post("/api/excuses/generate", json=REQUEST)

    assert response.status_code == 503
