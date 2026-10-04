"""Сценарии использования: связывают репозитории (БД) и чистую логику генератора."""

import random
from collections import Counter
from datetime import datetime, tzinfo

from sqlalchemy.orm import Session

from app import repositories as repo
from app.models import ExcuseHistory, ExcuseTemplate, User, utcnow
from app.schemas import ExcuseOut, HistoryItemOut, StatsOut
from app.services.context import RISK_WARNINGS, delay_category, risk_level, time_of_day
from app.services.generator import (
    ExcuseContext,
    HistoryEntry,
    TemplateData,
    generate,
    lateness_last_week,
)


class NotFoundError(Exception):
    """Запрошенный объект не найден."""


def _template_data(template: ExcuseTemplate) -> TemplateData:
    return TemplateData(
        id=template.id,
        text=template.text,
        theme=template.theme,
        subject_category=template.subject_category,
        min_delay=template.min_delay,
        max_delay=template.max_delay,
        time_of_day=template.time_of_day,
        credibility=template.credibility,
        base_weight=template.base_weight,
    )


def _history_entry(item: ExcuseHistory) -> HistoryEntry:
    return HistoryEntry(
        template_id=item.template_id,
        theme=item.template.theme,
        subject_name=item.subject.name,
        created_at=item.created_at,
        worked=item.worked,
    )


def _history_item_out(item: ExcuseHistory) -> HistoryItemOut:
    return HistoryItemOut(
        id=item.id,
        text=item.rendered_text,
        subject=item.subject.name,
        delay_minutes=item.delay_minutes,
        theme=item.template.theme,
        created_at=item.created_at,
        worked=item.worked,
    )


def _require_user(session: Session, username: str) -> User:
    user = repo.get_user(session, username)
    if user is None:
        raise NotFoundError(f"Пользователь «{username}» не найден")
    return user


def local_moment(at: datetime | None, tz: tzinfo) -> datetime:
    """Момент опоздания в часовом поясе вуза; время без пояса считается местным."""
    if at is None:
        return datetime.now(tz)
    if at.tzinfo is None:
        return at
    return at.astimezone(tz)


def generate_excuse(
    session: Session,
    username: str,
    subject_name: str,
    delay_minutes: int,
    tz: tzinfo,
    at: datetime | None = None,
    rng: random.Random | None = None,
) -> ExcuseOut:
    subject = repo.get_subject(session, subject_name)
    if subject is None:
        raise NotFoundError(f"Предмет «{subject_name}» не найден")
    user = repo.get_or_create_user(session, username)

    history = [_history_entry(item) for item in repo.user_history(session, user.id)]
    now = utcnow()
    weekly = lateness_last_week(history, now)
    risk = risk_level(weekly)
    ctx = ExcuseContext(
        subject_name=subject.name,
        subject_category=subject.category,
        delay_minutes=delay_minutes,
        time_of_day=time_of_day(local_moment(at, tz)),
        risk_level=risk,
    )
    templates = [_template_data(t) for t in repo.list_templates(session)]
    result = generate(templates, ctx, history, rng)

    item = repo.add_history(
        session,
        ExcuseHistory(
            user=user,
            template_id=result.template.id,
            subject=subject,
            delay_minutes=delay_minutes,
            rendered_text=result.text,
            created_at=now,
        ),
    )
    session.commit()

    return ExcuseOut(
        history_id=item.id,
        text=result.text,
        theme=result.template.theme,
        credibility=result.template.credibility,
        delay_category=delay_category(delay_minutes),
        time_of_day=ctx.time_of_day,
        risk_level=risk,
        lateness_last_week=weekly,
        warning=RISK_WARNINGS[risk],
    )


def get_history(session: Session, username: str) -> list[HistoryItemOut]:
    user = _require_user(session, username)
    return [_history_item_out(item) for item in repo.user_history(session, user.id)]


def set_feedback(session: Session, item_id: int, worked: bool) -> HistoryItemOut:
    item = repo.get_history_item(session, item_id)
    if item is None:
        raise NotFoundError(f"Запись истории {item_id} не найдена")
    item.worked = worked
    session.commit()
    return _history_item_out(item)


def get_stats(session: Session, username: str) -> StatsOut:
    user = _require_user(session, username)
    history = repo.user_history(session, user.id)
    rated = [item.worked for item in history if item.worked is not None]
    themes = Counter(item.template.theme for item in history)

    return StatsOut(
        username=user.username,
        total=len(history),
        last_week=lateness_last_week([_history_entry(item) for item in history], utcnow()),
        average_delay=(
            round(sum(item.delay_minutes for item in history) / len(history), 1)
            if history
            else None
        ),
        favorite_theme=themes.most_common(1)[0][0] if themes else None,
        success_rate=round(sum(rated) / len(rated), 2) if rated else None,
    )
