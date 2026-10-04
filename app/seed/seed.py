import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExcuseTemplate, Subject

SEED_DIR = Path(__file__).parent


def load_json(name: str) -> list[dict[str, Any]]:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def _upsert(session: Session, model: type, key: str, rows: list[dict[str, Any]]) -> int:
    """Добавляет новые записи и обновляет существующие по уникальному полю key."""
    existing = {getattr(obj, key): obj for obj in session.scalars(select(model))}
    created = 0
    for row in rows:
        obj = existing.get(row[key])
        if obj is None:
            session.add(model(**row))
            created += 1
        else:
            for field, value in row.items():
                setattr(obj, field, value)
    return created


def seed(session: Session) -> dict[str, int]:
    """Идемпотентно заполняет справочники; повторный запуск не создаёт дублей."""
    result = {
        "subjects": _upsert(session, Subject, "name", load_json("subjects.json")),
        "templates": _upsert(session, ExcuseTemplate, "text", load_json("excuses.json")),
    }
    session.commit()
    return result
