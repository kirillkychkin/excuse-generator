from datetime import datetime

import pytest

from app.enums import DelayCategory, RiskLevel, TimeOfDay
from app.services.context import (
    RISK_WARNINGS,
    delay_category,
    format_minutes,
    risk_level,
    time_of_day,
)


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (1, DelayCategory.SMALL),
        (5, DelayCategory.SMALL),
        (6, DelayCategory.MEDIUM),
        (15, DelayCategory.MEDIUM),
        (16, DelayCategory.LARGE),
        (40, DelayCategory.LARGE),
        (41, DelayCategory.HUGE),
        (180, DelayCategory.HUGE),
    ],
)
def test_delay_category_bounds(minutes, expected):
    assert delay_category(minutes) == expected


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (5, TimeOfDay.MORNING),
        (11, TimeOfDay.MORNING),
        (12, TimeOfDay.DAY),
        (16, TimeOfDay.DAY),
        (17, TimeOfDay.EVENING),
        (23, TimeOfDay.EVENING),
        (2, TimeOfDay.EVENING),
    ],
)
def test_time_of_day_by_hour(hour, expected):
    assert time_of_day(datetime(2026, 10, 5, hour, 30)) == expected


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (1, "1 минуту"),
        (2, "2 минуты"),
        (5, "5 минут"),
        (11, "11 минут"),
        (12, "12 минут"),
        (21, "21 минуту"),
        (22, "22 минуты"),
        (111, "111 минут"),
    ],
)
def test_format_minutes_declension(minutes, expected):
    assert format_minutes(minutes) == expected


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, RiskLevel.LOW),
        (1, RiskLevel.LOW),
        (2, RiskLevel.MEDIUM),
        (3, RiskLevel.MEDIUM),
        (4, RiskLevel.HIGH),
        (10, RiskLevel.HIGH),
    ],
)
def test_risk_level_by_weekly_count(count, expected):
    assert risk_level(count) == expected


def test_only_low_risk_has_no_warning():
    assert RISK_WARNINGS[RiskLevel.LOW] is None
    assert RISK_WARNINGS[RiskLevel.MEDIUM]
    assert RISK_WARNINGS[RiskLevel.HIGH]
