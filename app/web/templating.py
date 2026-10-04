from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=BASE_DIR / "templates")

THEME_LABELS = {
    "transport": "Транспорт",
    "health": "Здоровье",
    "tech": "Техника",
    "family": "Дом и семья",
    "weather": "Погода",
    "bureaucracy": "Организационное",
    "study": "Учёба",
    "absurd": "Абсурд",
}
RISK_LABELS = {"low": "низкий", "medium": "средний", "high": "высокий"}
DELAY_LABELS = {
    "small": "небольшое",
    "medium": "среднее",
    "large": "большое",
    "huge": "огромное",
}

templates.env.filters["theme"] = lambda value: THEME_LABELS.get(value, value)
templates.env.filters["risk"] = lambda value: RISK_LABELS.get(value, value)
templates.env.filters["delay"] = lambda value: DELAY_LABELS.get(value, value)
