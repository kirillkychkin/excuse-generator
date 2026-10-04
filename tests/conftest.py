import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  — регистрирует модели в Base.metadata
from app.config import Settings
from app.db import Base, get_session
from app.main import create_app
from app.seed.seed import seed


@pytest.fixture
def engine() -> Iterator[Engine]:
    """SQLite в памяти; TEST_DATABASE_URL позволяет прогнать тесты на настоящей СУБД."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        engine = create_engine(Settings(database_url=url).database_url)
    else:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def seeded_session(session: Session) -> Session:
    seed(session)
    return session


@pytest.fixture
def client(seeded_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: seeded_session
    with TestClient(app) as client:
        yield client
