"""Подбор оправдания: фильтрация шаблонов, расчёт весов и случайный выбор.

Модуль не зависит от БД: шаблоны и история передаются простыми dataclass-объектами,
а генератор случайных чисел — параметром, поэтому логику легко тестировать.
"""

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.enums import RiskLevel, TimeOfDay
from app.services.context import format_minutes

RECENT_TEMPLATES_LIMIT = 5
HIGH_RISK_MIN_CREDIBILITY = 4
RECENT_THEMES_LIMIT = 3
RECENT_THEME_PENALTY = 0.3
SAME_SUBJECT_PENALTY = 0.2
WORKED_BONUS = 1.5
FAILED_PENALTY = 0.1


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

    # Учитываем последнюю оценку пользователя: «сработало» или «не сработало»
    feedback = next(
        (e.worked for e in history if e.template_id == template.id and e.worked is not None),
        None,
    )
    if feedback is True:
        weight *= WORKED_BONUS
    elif feedback is False:
        weight *= FAILED_PENALTY

    # При частых опозданиях убедительность важнее разнообразия
    if ctx.risk_level != RiskLevel.LOW:
        weight *= template.credibility / 3

    return weight


def lateness_last_week(history: Sequence[HistoryEntry], now: datetime) -> int:
    """Сколько раз пользователь опаздывал за последние 7 дней."""
    week_ago = now - timedelta(days=7)
    return sum(1 for entry in history if entry.created_at >= week_ago)


@dataclass(frozen=True)
class GeneratedExcuse:
    template: TemplateData
    text: str


class NoTemplatesError(Exception):
    """В базе нет ни одного шаблона оправдания."""


def render(template: TemplateData, ctx: ExcuseContext, rng: random.Random) -> str:
    """Подставляет в шаблон время опоздания, предмет и случайный номер автобуса."""
    return template.text.format(
        minutes=format_minutes(ctx.delay_minutes),
        subject=ctx.subject_name,
        bus=rng.randint(1, 99),
    )


def generate(
    templates: Sequence[TemplateData],
    ctx: ExcuseContext,
    history: Sequence[HistoryEntry] = (),
    rng: random.Random | None = None,
) -> GeneratedExcuse:
    """Выбирает оправдание взвешенным случайным выбором среди подходящих шаблонов."""
    rng = rng or random.Random()
    candidates = filter_candidates(templates, ctx, history)
    if not candidates:
        raise NoTemplatesError("Нет шаблонов оправданий — заполните базу командой seed")
    weights = [template_weight(t, ctx, history) for t in candidates]
    chosen = rng.choices(candidates, weights=weights, k=1)[0]
    return GeneratedExcuse(template=chosen, text=render(chosen, ctx, rng))
