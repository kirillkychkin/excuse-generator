from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import repositories as repo
from app.db import get_session
from app.schemas import (
    SubjectOut,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]


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
