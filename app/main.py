from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.services.excuses import NotFoundError
from app.services.generator import NoTemplatesError
from app.web.routes import router as web_router
from app.web.templating import STATIC_DIR


def create_app() -> FastAPI:
    app = FastAPI(
        title="Генератор оправданий опоздания",
        description="Подбирает оправдание опоздания с учётом контекста и истории пользователя.",
        version="0.1.0",
    )

    @app.exception_handler(NotFoundError)
    def not_found(request: Request, error: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(NoTemplatesError)
    def no_templates(request: Request, error: NoTemplatesError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @app.get("/health", tags=["service"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(api_router)
    app.include_router(web_router)
    return app


app = create_app()
