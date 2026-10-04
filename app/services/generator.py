"""Подбор оправдания: фильтрация шаблонов, расчёт весов и случайный выбор.

Модуль не зависит от БД: шаблоны и история передаются простыми dataclass-объектами,
а генератор случайных чисел — параметром, поэтому логику легко тестировать.
"""
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from app.enums import RiskLevel, TimeOfDay

RECENT_TEMPLATES_LIMIT = 5
HIGH_RISK_MIN_CREDIBILITY = 4
RECENT_THEMES_LIMIT = 3
RECENT_THEME_PENALTY = 0.3
SAME_SUBJECT_PENALTY = 0.2


@dataclass(frozen=True)
class TemplateData:
    id: int
    text: str
    theme: str
    subject_category: str | None
    min_delay: int
    max_delay: int
    time_of_day: str
    credibility: int
    base_weight: float = 1.0


@dataclass(frozen=True)
class HistoryEntry:
    template_id: int
    theme: str
    subject_name: str
    created_at: datetime
    worked: bool | None = None


@dataclass(frozen=True)
class ExcuseContext:
    subject_name: str
    subject_category: str
    delay_minutes: int
    time_of_day: TimeOfDay
    risk_level: RiskLevel


Check = Callable[[TemplateData], bool]


def _checks(ctx: ExcuseContext, history: Sequence[HistoryEntry]) -> list[Check]:
    """Условия отбора в порядке убывания важности."""
    recent_ids = {entry.template_id for entry in history[:RECENT_TEMPLATES_LIMIT]}
    min_credibility = HIGH_RISK_MIN_CREDIBILITY if ctx.risk_level == RiskLevel.HIGH else 1
    return [
        lambda t: t.min_delay <= ctx.delay_minutes <= t.max_delay,
        lambda t: t.subject_category in (None, ctx.subject_category),
        lambda t: t.id not in recent_ids,
        lambda t: t.credibility >= min_credibility,
        lambda t: t.time_of_day in (TimeOfDay.ANY, ctx.time_of_day),
    ]


def filter_candidates(
    templates: Sequence[TemplateData],
    ctx: ExcuseContext,
    history: Sequence[HistoryEntry] = (),
) -> list[TemplateData]:
    """Отбирает подходящие шаблоны; если не подошёл ни один, ослабляет наименее важные условия.

    history должна быть отсортирована от новых записей к старым.
    """
    checks = _checks(ctx, history)
    for active in range(len(checks), -1, -1):
        candidates = [t for t in templates if all(check(t) for check in checks[:active])]
        if candidates:
            return candidates
    return []


def template_weight(
    template: TemplateData,
    ctx: ExcuseContext,
    history: Sequence[HistoryEntry] = (),
) -> float:
    """Вес шаблона при случайном выборе: чем больше, тем вероятнее выбор."""
    weight = template.base_weight

    recent_themes = {entry.theme for entry in history[:RECENT_THEMES_LIMIT]}
    if template.theme in recent_themes:
        weight *= RECENT_THEME_PENALTY

    # Преподаватель этого предмета уже слышал такое оправдание
    if any(
        entry.template_id == template.id and entry.subject_name == ctx.subject_name
        for entry in history
    ):
        weight *= SAME_SUBJECT_PENALTY
    return weight
