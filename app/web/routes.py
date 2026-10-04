from typing import Annotated
from urllib.parse import quote, unquote

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import repositories as repo
from app.config import Settings, get_settings
from app.db import get_session
from app.schemas import GenerateRequest
from app.services import excuses
from app.services.excuses import NotFoundError
from app.web.templating import templates

router = APIRouter(include_in_schema=False)
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
USERNAME_COOKIE = "username"
DEFAULT_DELAY = 10


def _render_index(request: Request, session: Session, form: dict, status_code: int = 200, **ctx):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"subjects": repo.list_subjects(session), "form": form, "username": form["username"]} | ctx,
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    session: SessionDep,
    username: Annotated[str | None, Cookie(alias=USERNAME_COOKIE)] = None,
):
    form = {
        "username": unquote(username) if username else "",
        "subject": None,
        "delay_minutes": DEFAULT_DELAY,
    }
    return _render_index(request, session, form)


@router.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    username: Annotated[str, Form()],
    subject: Annotated[str, Form()],
    delay_minutes: Annotated[int, Form()],
):
    form = {"username": username.strip(), "subject": subject, "delay_minutes": delay_minutes}
    try:
        data = GenerateRequest(username=username, subject=subject, delay_minutes=delay_minutes)
        result = excuses.generate_excuse(
            session,
            username=data.username,
            subject_name=data.subject,
            delay_minutes=data.delay_minutes,
            tz=settings.tz,
        )
    except ValidationError:
        error = "Проверьте данные: имя от 2 до 50 символов, опоздание от 1 до 180 минут."
        return _render_index(request, session, form, status_code=422, error=error)
    except NotFoundError as exc:
        return _render_index(request, session, form, status_code=404, error=str(exc))

    response = _render_index(request, session, form, result=result)
    # Кириллицу в cookie нужно кодировать
    response.set_cookie(USERNAME_COOKIE, quote(data.username), max_age=365 * 24 * 3600)
    return response


@router.post("/feedback/{item_id}")
def feedback(item_id: int, worked: Annotated[bool, Form()], session: SessionDep):
    try:
        excuses.set_feedback(session, item_id, worked)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    username = repo.get_history_item(session, item_id).user.username
    return RedirectResponse(f"/history/{quote(username)}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/history/{username}", response_class=HTMLResponse)
def history(request: Request, username: str, session: SessionDep):
    try:
        stats = excuses.get_stats(session, username)
        items = excuses.get_history(session, username)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "history.html",
        {"username": username, "stats": stats, "history": items},
    )
