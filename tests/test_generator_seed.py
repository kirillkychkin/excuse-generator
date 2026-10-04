"""Проверка генератора на реальных шаблонах из seed-данных."""

import random

import pytest

from app.enums import RiskLevel, SubjectCategory, TimeOfDay
from app.seed.seed import load_json
from app.services.generator import ExcuseContext, TemplateData, filter_candidates, generate

TEMPLATES = [TemplateData(id=i, **row) for i, row in enumerate(load_json("excuses.json"), 1)]
DELAYS = [1, 3, 5, 10, 15, 25, 40, 60, 120, 180]


@pytest.mark.parametrize("category", list(SubjectCategory))
@pytest.mark.parametrize("tod", [TimeOfDay.MORNING, TimeOfDay.DAY, TimeOfDay.EVENING])
def test_every_situation_gets_rendered_excuse(category, tod):
    for delay in DELAYS:
        ctx = ExcuseContext("Предмет", category, delay, tod, RiskLevel.LOW)

        result = generate(TEMPLATES, ctx, rng=random.Random(delay))

        assert "{" not in result.text


@pytest.mark.parametrize("delay", DELAYS)
def test_seed_has_credible_excuse_for_every_delay(delay):
    ctx = ExcuseContext("Предмет", SubjectCategory.MATH, delay, TimeOfDay.DAY, RiskLevel.HIGH)

    candidates = filter_candidates(TEMPLATES, ctx)

    assert all(t.min_delay <= delay <= t.max_delay for t in candidates)
    assert all(t.credibility >= 4 for t in candidates)
