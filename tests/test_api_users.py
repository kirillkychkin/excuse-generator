def test_list_subjects(client):
    response = client.get("/api/subjects")

    assert response.status_code == 200
    subjects = response.json()
    assert len(subjects) == 12
    assert {"name": "Физика", "category": "science"}.items() <= next(
        s for s in subjects if s["name"] == "Физика"
    ).items()


def test_create_user(client):
    response = client.post("/api/users", json={"username": "  kirill  "})

    assert response.status_code == 201
    assert response.json()["username"] == "kirill"


def test_create_duplicate_user(client):
    client.post("/api/users", json={"username": "kirill"})

    response = client.post("/api/users", json={"username": "kirill"})

    assert response.status_code == 409


def test_create_user_validates_name(client):
    response = client.post("/api/users", json={"username": "k"})

    assert response.status_code == 422


def test_get_user(client):
    client.post("/api/users", json={"username": "kirill"})

    response = client.get("/api/users/kirill")

    assert response.status_code == 200
    assert response.json()["username"] == "kirill"


def test_get_unknown_user(client):
    assert client.get("/api/users/nobody").status_code == 404
