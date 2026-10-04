from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import repositories as repo
from app.config import Settings, get_settings
from app.db import get_session
from app.schemas import (
    ExcuseOut,
    FeedbackRequest,
    GenerateRequest,
    HistoryItemOut,
    SubjectOut,
    UserCreate,
    UserOut,
)
from app.services import excuses

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/subjects", response_model=list[SubjectOut], tags=["subjects"])
def list_subjects(session: SessionDep):
    """Справочник предметов."""
    return repo.list_subjects(session)


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(data: UserCreate, session: SessionDep):
    if repo.get_user(session, data.username) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь уже существует")
    user = repo.get_or_create_user(session, data.username)
    session.commit()
    return user


@router.get("/users/{username}", response_model=UserOut, tags=["users"])
def get_user(username: str, session: SessionDep):
    user = repo.get_user(session, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.post("/excuses/generate", response_model=ExcuseOut, tags=["excuses"])
def generate_excuse(data: GenerateRequest, session: SessionDep, settings: SettingsDep):
    """Подбирает оправдание с учётом предмета, времени опоздания и истории пользователя.

    Пользователь создаётся автоматически при первой генерации.
    """
    return excuses.generate_excuse(
        session,
        username=data.username,
        subject_name=data.subject,
        delay_minutes=data.delay_minutes,
        tz=settings.tz,
        at=data.at,
    )


@router.get(
    "/users/{username}/history",
    response_model=list[HistoryItemOut],
    tags=["history"],
)
def user_history(username: str, session: SessionDep):
    """История оправданий пользователя, от новых к старым."""
    return excuses.get_history(session, username)


@router.post("/history/{item_id}/feedback", response_model=HistoryItemOut, tags=["history"])
def feedback(item_id: int, data: FeedbackRequest, session: SessionDep):
    """Отметить, сработало ли оправдание; оценка влияет на следующие генерации."""
    return excuses.set_feedback(session, item_id, data.worked)
