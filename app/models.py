from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    """Время в UTC без tzinfo — одинаково хранится и в SQLite, и в PostgreSQL."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    history: Mapped[list["ExcuseHistory"]] = relationship(back_populates="user")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(20))


class ExcuseTemplate(Base):
    __tablename__ = "excuse_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, unique=True)
    theme: Mapped[str] = mapped_column(String(20))
    # None — шаблон подходит для любого предмета
    subject_category: Mapped[str | None] = mapped_column(String(20))
    min_delay: Mapped[int] = mapped_column(Integer)
    max_delay: Mapped[int] = mapped_column(Integer)
    time_of_day: Mapped[str] = mapped_column(String(10), default="any")
    credibility: Mapped[int] = mapped_column(Integer)
    base_weight: Mapped[float] = mapped_column(Float, default=1.0)


class ExcuseHistory(Base):
    __tablename__ = "excuse_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("excuse_templates.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    delay_minutes: Mapped[int] = mapped_column(Integer)
    rendered_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    # None — пользователь ещё не оценил оправдание
    worked: Mapped[bool | None] = mapped_column(Boolean)

    user: Mapped[User] = relationship(back_populates="history")
    template: Mapped[ExcuseTemplate] = relationship()
    subject: Mapped[Subject] = relationship()
