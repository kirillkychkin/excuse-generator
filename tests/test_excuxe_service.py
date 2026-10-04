import random
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app import repositories
from app.enums import RiskLevel, TimeOfDay
from app.models import ExcuseHistory
from app.services import excuses
from app.services.excuses import NotFoundError

TZ = ZoneInfo("Asia/Yakutsk")
MORNING = datetime(2026, 10, 5, 9, 0)


def generate(session, username="kirill", subject="Философия", delay=10, seed=0):
    return excuses.generate_excuse(
        session, username, subject, delay, tz=TZ, at=MORNING, rng=random.Random(seed)
    )


def test_generate_creates_user_and_history(seeded_session):
    result = generate(seeded_session)

    history = excuses.get_history(seeded_session, "kirill")
    assert [h.id for h in history] == [result.history_id]
    assert history[0].text == result.text
    assert result.time_of_day == TimeOfDay.MORNING
    assert result.risk_level == RiskLevel.LOW
    assert result.warning is None


def test_generate_unknown_subject(seeded_session):
    with pytest.raises(NotFoundError):
        generate(seeded_session, subject="Астрология")


def test_consecutive_excuses_do_not_repeat(seeded_session):
    texts = [generate(seeded_session, seed=i).text for i in range(5)]

    assert len(set(texts)) == 5


def test_frequent_lateness_raises_risk(seeded_session):
    results = [generate(seeded_session, seed=i) for i in range(5)]

    assert [r.lateness_last_week for r in results] == [0, 1, 2, 3, 4]
    assert results[2].risk_level == RiskLevel.MEDIUM
    assert results[4].risk_level == RiskLevel.HIGH
    assert results[4].warning
    assert results[4].credibility >= 4


def test_old_lateness_does_not_raise_risk(seeded_session):
    for i in range(4):
        old = generate(seeded_session, seed=i)
        item = seeded_session.get(ExcuseHistory, old.history_id)
        item.created_at -= timedelta(days=10)
    seeded_session.commit()

    result = generate(seeded_session)

    assert result.lateness_last_week == 0
    assert result.risk_level == RiskLevel.LOW


def test_feedback_is_saved(seeded_session):
    result = generate(seeded_session)

    item = excuses.set_feedback(seeded_session, result.history_id, worked=True)

    assert item.worked is True
    assert excuses.get_history(seeded_session, "kirill")[0].worked is True


def test_feedback_for_unknown_item(seeded_session):
    with pytest.raises(NotFoundError):
        excuses.set_feedback(seeded_session, 999, worked=False)


def test_history_of_unknown_user(seeded_session):
    with pytest.raises(NotFoundError):
        excuses.get_history(seeded_session, "nobody")


def test_stats(seeded_session):
    first = generate(seeded_session, delay=10)
    generate(seeded_session, delay=20, seed=1)
    excuses.set_feedback(seeded_session, first.history_id, worked=True)

    stats = excuses.get_stats(seeded_session, "kirill")

    assert stats.total == 2
    assert stats.last_week == 2
    assert stats.average_delay == 15.0
    assert stats.favorite_theme is not None
    assert stats.success_rate == 1.0


def test_stats_without_history(seeded_session):
    repositories.get_or_create_user(seeded_session, "newbie")

    stats = excuses.get_stats(seeded_session, "newbie")

    assert stats.total == 0
    assert stats.average_delay is None
    assert stats.favorite_theme is None
    assert stats.success_rate is None


@pytest.mark.parametrize(
    ("at", "expected_hour"),
    [
        (datetime(2026, 10, 5, 9, 0), 9),  # без пояса — местное время
        (datetime(2026, 10, 5, 0, 30, tzinfo=UTC), 9),  # UTC+9
    ],
)
def test_local_moment(at, expected_hour):
    assert excuses.local_moment(at, TZ).hour == expected_hour


def test_local_moment_defaults_to_now():
    assert excuses.local_moment(None, TZ).tzinfo == TZ
