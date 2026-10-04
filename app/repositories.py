"""Доступ к данным: все SQL-запросы приложения собраны здесь."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import ExcuseHistory, ExcuseTemplate, Subject, User


def get_user(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_or_create_user(session: Session, username: str) -> User:
    user = get_user(session, username)
    if user is None:
        user = User(username=username)
        session.add(user)
        session.flush()
    return user


def list_subjects(session: Session) -> list[Subject]:
    return list(session.scalars(select(Subject).order_by(Subject.name)))


def get_subject(session: Session, name: str) -> Subject | None:
    return session.scalar(select(Subject).where(Subject.name == name))


def list_templates(session: Session) -> list[ExcuseTemplate]:
    return list(session.scalars(select(ExcuseTemplate)))


def user_history(session: Session, user_id: int) -> list[ExcuseHistory]:
    """История пользователя от новых записей к старым."""
    query = (
        select(ExcuseHistory)
        .where(ExcuseHistory.user_id == user_id)
        .options(joinedload(ExcuseHistory.template), joinedload(ExcuseHistory.subject))
        .order_by(ExcuseHistory.created_at.desc(), ExcuseHistory.id.desc())
    )
    return list(session.scalars(query))


def get_history_item(session: Session, item_id: int) -> ExcuseHistory | None:
    return session.get(ExcuseHistory, item_id)


def add_history(session: Session, item: ExcuseHistory) -> ExcuseHistory:
    session.add(item)
    session.flush()
    return item
