from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(
        title="Генератор оправданий опоздания",
        description="Подбирает оправдание опоздания с учётом контекста и истории пользователя.",
        version="0.1.0",
    )

    @app.get("/health", tags=["service"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app

app = create_app()
