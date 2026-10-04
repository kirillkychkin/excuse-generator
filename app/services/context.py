from datetime import datetime

from app.enums import DelayCategory, RiskLevel, TimeOfDay


def delay_category(minutes: int) -> DelayCategory:
    if minutes <= 5:
        return DelayCategory.SMALL
    if minutes <= 15:
        return DelayCategory.MEDIUM
    if minutes <= 40:
        return DelayCategory.LARGE
    return DelayCategory.HUGE


def time_of_day(moment: datetime) -> TimeOfDay:
    """Утро — с 5 до 12, день — с 12 до 17, остальное время считается вечером."""
    if 5 <= moment.hour < 12:
        return TimeOfDay.MORNING
    if 12 <= moment.hour < 17:
        return TimeOfDay.DAY
    return TimeOfDay.EVENING


def format_minutes(minutes: int) -> str:
    """Склоняет слово «минута»: 1 минуту, 3 минуты, 11 минут, 21 минуту."""
    if minutes % 10 == 1 and minutes % 100 != 11:
        word = "минуту"
    elif minutes % 10 in (2, 3, 4) and minutes % 100 not in (12, 13, 14):
        word = "минуты"
    else:
        word = "минут"
    return f"{minutes} {word}"


RISK_WARNINGS = {
    RiskLevel.LOW: None,
    RiskLevel.MEDIUM: "Вы уже опаздывали на этой неделе — выбирайте оправдание аккуратнее.",
    RiskLevel.HIGH: (
        "Слишком много опозданий за неделю: преподаватель может не поверить. "
        "Подобраны только самые убедительные варианты — а лучше просто приходите вовремя."
    ),
}


def risk_level(lateness_last_week: int) -> RiskLevel:
    """Уровень риска по числу опозданий за последние 7 дней (не считая текущего)."""
    if lateness_last_week < 2:
        return RiskLevel.LOW
    if lateness_last_week < 4:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH
