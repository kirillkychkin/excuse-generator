from datetime import datetime, timedelta

import pytest

from app.enums import RiskLevel, TimeOfDay
from app.services.generator import (
    ExcuseContext,
    HistoryEntry,
    TemplateData,
    filter_candidates,
    template_weight,
)

NOW = datetime(2026, 10, 5, 9, 0)


def make_template(id: int, **overrides) -> TemplateData:
    fields = {
        "text": f"Оправдание {id}",
        "theme": "transport",
        "subject_category": None,
        "min_delay": 1,
        "max_delay": 180,
        "time_of_day": "any",
        "credibility": 3,
    }
    fields.update(overrides)
    return TemplateData(id=id, **fields)


def make_ctx(**overrides) -> ExcuseContext:
    fields = {
        "subject_name": "Философия",
        "subject_category": "humanities",
        "delay_minutes": 10,
        "time_of_day": TimeOfDay.MORNING,
        "risk_level": RiskLevel.LOW,
    }
    fields.update(overrides)
    return ExcuseContext(**fields)


def make_entry(template_id: int, theme: str = "transport", **overrides) -> HistoryEntry:
    fields = {"subject_name": "Философия", "created_at": NOW - timedelta(days=1)}
    fields.update(overrides)
    return HistoryEntry(template_id=template_id, theme=theme, **fields)


def ids(templates) -> set[int]:
    return {t.id for t in templates}


class TestFilterCandidates:
    def test_filters_by_delay_range(self):
        templates = [
            make_template(1, min_delay=1, max_delay=5),
            make_template(2, min_delay=6, max_delay=15),
            make_template(3, min_delay=16, max_delay=40),
        ]

        assert ids(filter_candidates(templates, make_ctx(delay_minutes=10))) == {2}

    def test_keeps_universal_and_matching_subject_templates(self):
        templates = [
            make_template(1, subject_category=None),
            make_template(2, subject_category="humanities"),
            make_template(3, subject_category="programming"),
        ]

        assert ids(filter_candidates(templates, make_ctx())) == {1, 2}

    def test_filters_by_time_of_day(self):
        templates = [
            make_template(1, time_of_day="morning"),
            make_template(2, time_of_day="evening"),
            make_template(3, time_of_day="any"),
        ]

        result = filter_candidates(templates, make_ctx(time_of_day=TimeOfDay.EVENING))

        assert ids(result) == {2, 3}

    def test_excludes_recently_used_templates(self):
        templates = [make_template(i) for i in range(1, 8)]
        history = [make_entry(i) for i in (1, 2, 3, 4, 5, 6)]

        result = filter_candidates(templates, make_ctx(), history)

        # Исключаются только 5 последних шаблонов, шестой по давности снова доступен
        assert ids(result) == {6, 7}

    def test_high_risk_keeps_only_credible_templates(self):
        templates = [make_template(1, credibility=2), make_template(2, credibility=5)]

        result = filter_candidates(templates, make_ctx(risk_level=RiskLevel.HIGH))

        assert ids(result) == {2}

    def test_relaxes_time_of_day_first(self):
        templates = [make_template(1, time_of_day="evening", credibility=5)]

        result = filter_candidates(templates, make_ctx(risk_level=RiskLevel.HIGH))

        assert ids(result) == {1}

    def test_relaxes_recent_exclusion_when_nothing_left(self):
        templates = [make_template(1), make_template(2)]
        history = [make_entry(1), make_entry(2)]

        assert ids(filter_candidates(templates, make_ctx(), history)) == {1, 2}

    def test_falls_back_to_all_templates(self):
        templates = [make_template(1, min_delay=1, max_delay=5)]

        assert ids(filter_candidates(templates, make_ctx(delay_minutes=100))) == {1}

    def test_empty_templates_give_empty_result(self):
        assert filter_candidates([], make_ctx()) == []


class TestTemplateWeight:
    def test_base_weight_without_history(self):
        assert template_weight(make_template(1, base_weight=2.0), make_ctx()) == 2.0

    def test_penalizes_recent_theme(self):
        history = [make_entry(10, theme="health"), make_entry(11, theme="transport")]

        weight = template_weight(make_template(1, theme="transport"), make_ctx(), history)

        assert weight == pytest.approx(0.3)

    def test_old_theme_is_not_penalized(self):
        history = [make_entry(i, theme="health") for i in (10, 11, 12)]
        history.append(make_entry(13, theme="transport"))

        weight = template_weight(make_template(1, theme="transport"), make_ctx(), history)

        assert weight == 1.0

    def test_penalizes_template_used_for_same_subject(self):
        history = [make_entry(i, theme="health") for i in (10, 11, 12)]
        history.append(make_entry(1, theme="transport", subject_name="Философия"))

        weight = template_weight(make_template(1), make_ctx(subject_name="Философия"), history)

        assert weight == pytest.approx(0.2)

    def test_template_used_for_other_subject_is_not_penalized(self):
        history = [make_entry(i, theme="health") for i in (10, 11, 12)]
        history.append(make_entry(1, subject_name="Физика"))

        weight = template_weight(make_template(1), make_ctx(subject_name="Философия"), history)

        assert weight == 1.0

    def _feedback_history(self, *worked_values):
        """Старые записи по шаблону 1 для другого предмета — влияет только оценка."""
        history = [make_entry(i, theme="health") for i in (10, 11, 12)]
        history += [make_entry(1, subject_name="Физика", worked=w) for w in worked_values]
        return history
