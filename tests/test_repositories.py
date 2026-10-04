from datetime import datetime

from app import repositories as repo
from app.models import ExcuseHistory
from app.seed.seed import seed


def test_get_or_create_user_returns_same_user(session):
    first = repo.get_or_create_user(session, "kirill")
    second = repo.get_or_create_user(session, "kirill")

    assert first.id == second.id


def test_get_unknown_user_returns_none(session):
    assert repo.get_user(session, "nobody") is None


def test_subjects_are_sorted_by_name(session):
    seed(session)

    names = [s.name for s in repo.list_subjects(session)]

    assert names == sorted(names)
    assert repo.get_subject(session, "Философия").category == "humanities"


def test_user_history_is_newest_first(session):
    seed(session)
    user = repo.get_or_create_user(session, "kirill")
    subject = repo.get_subject(session, "Физика")
    template = repo.list_templates(session)[0]
    for day in (1, 3, 2):
        repo.add_history(
            session,
            ExcuseHistory(
                user=user,
                template=template,
                subject=subject,
                delay_minutes=day,
                rendered_text="text",
                created_at=datetime(2026, 10, day),
            ),
        )

    history = repo.user_history(session, user.id)

    assert [h.delay_minutes for h in history] == [3, 2, 1]
    assert history[0].subject.name == "Физика"
