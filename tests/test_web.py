from urllib.parse import quote

FORM = {"username": "Кирилл", "subject": "Базы данных", "delay_minutes": "20"}


def test_index_shows_form_with_subjects(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Придумать оправдание" in response.text
    assert "Базы данных" in response.text


def test_generate_shows_excuse_and_remembers_name(client):
    response = client.post("/generate", data=FORM)

    assert response.status_code == 200
    assert 'class="excuse"' in response.text
    assert "Риск: низкий" in response.text
    assert response.cookies["username"] == quote("Кирилл")


def test_index_prefills_name_from_cookie(client):
    client.post("/generate", data=FORM)

    response = client.get("/")

    assert 'value="Кирилл"' in response.text


def test_generate_with_invalid_delay_shows_error(client):
    response = client.post("/generate", data={**FORM, "delay_minutes": "500"})

    assert response.status_code == 422
    assert 'class="error"' in response.text


def test_generate_with_unknown_subject_shows_error(client):
    response = client.post("/generate", data={**FORM, "subject": "Астрология"})

    assert response.status_code == 404
    assert "Астрология" in response.text


def test_static_styles_are_served(client):
    assert client.get("/static/style.css").status_code == 200


def generate_and_get_id(client) -> int:
    client.post("/generate", data=FORM)
    return client.get(f"/api/users/{FORM['username']}/history").json()[0]["id"]


def test_feedback_redirects_to_history(client):
    item_id = generate_and_get_id(client)

    response = client.post(f"/feedback/{item_id}", data={"worked": "true"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/history/{quote('Кирилл')}"


def test_feedback_for_unknown_item(client):
    assert client.post("/feedback/999", data={"worked": "true"}).status_code == 404


def test_history_page_shows_stats_and_items(client):
    item_id = generate_and_get_id(client)
    client.post(f"/feedback/{item_id}", data={"worked": "true"})

    response = client.get(f"/history/{quote('Кирилл')}")

    assert response.status_code == 200
    assert "Кирилл: статистика опозданий" in response.text
    assert "Базы данных" in response.text
    assert "100%" in response.text
    assert "сработало" in response.text


def test_history_page_for_new_user(client):
    client.post("/api/users", json={"username": "newbie"})

    response = client.get("/history/newbie")

    assert "Опозданий пока не было" in response.text


def test_history_page_for_unknown_user(client):
    assert client.get("/history/nobody").status_code == 404
