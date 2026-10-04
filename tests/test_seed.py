from sqlalchemy import func, select

from app.enums import SubjectCategory, Theme, TimeOfDay
from app.models import ExcuseTemplate, Subject
from app.seed.seed import load_json, seed


def test_seed_creates_all_rows(session):
    created = seed(session)

    assert created["subjects"] == len(load_json("subjects.json"))
    assert created["templates"] == len(load_json("excuses.json"))


def test_seed_is_idempotent(session):
    seed(session)
    second = seed(session)

    assert second == {"subjects": 0, "templates": 0}
    assert session.scalar(select(func.count()).select_from(Subject)) == len(
        load_json("subjects.json")
    )


def test_seed_templates_use_known_values():
    for row in load_json("excuses.json"):
        assert Theme(row["theme"])
        assert TimeOfDay(row["time_of_day"])
        if row["subject_category"] is not None:
            assert SubjectCategory(row["subject_category"])
        assert 1 <= row["min_delay"] <= row["max_delay"] <= 180
        assert 1 <= row["credibility"] <= 5


def test_seed_updates_changed_template(session):
    seed(session)
    template = session.scalars(select(ExcuseTemplate)).first()
    template.credibility = 1
    session.commit()

    seed(session)

    original = next(r for r in load_json("excuses.json") if r["text"] == template.text)
    assert template.credibility == original["credibility"]
