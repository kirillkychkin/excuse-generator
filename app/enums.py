from enum import StrEnum


class SubjectCategory(StrEnum):
    PROGRAMMING = "programming"
    MATH = "math"
    PE = "pe"
    HUMANITIES = "humanities"
    SCIENCE = "science"


class Theme(StrEnum):
    TRANSPORT = "transport"
    HEALTH = "health"
    TECH = "tech"
    FAMILY = "family"
    WEATHER = "weather"
    BUREAUCRACY = "bureaucracy"
    STUDY = "study"
    ABSURD = "absurd"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    ANY = "any"


class DelayCategory(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
