from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.enums import DelayCategory, RiskLevel, TimeOfDay

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]


class UserCreate(BaseModel):
    username: Username


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str


class GenerateRequest(BaseModel):
    username: Username
    subject: str = Field(description="Название предмета из справочника /api/subjects")
    delay_minutes: int = Field(ge=1, le=180, description="На сколько минут опоздание")
    at: datetime | None = Field(
        default=None,
        description="Момент опоздания; по умолчанию — текущее время в часовом поясе вуза",
    )


class ExcuseOut(BaseModel):
    history_id: int
    text: str
    theme: str
    credibility: int
    delay_category: DelayCategory
    time_of_day: TimeOfDay
    risk_level: RiskLevel
    lateness_last_week: int
    warning: str | None


class HistoryItemOut(BaseModel):
    id: int
    text: str
    subject: str
    delay_minutes: int
    theme: str
    created_at: datetime
    worked: bool | None


class FeedbackRequest(BaseModel):
    worked: bool


class StatsOut(BaseModel):
    username: str
    total: int
    last_week: int
    average_delay: float | None
    favorite_theme: str | None
    success_rate: float | None = Field(description="Доля сработавших среди оценённых, 0–1")
