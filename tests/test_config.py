import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "raw",
    ["postgres://u:p@host:5432/db", "postgresql://u:p@host:5432/db"],
)
def test_postgres_url_gets_psycopg_driver(raw):
    settings = Settings(database_url=raw)

    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_default_timezone_is_yakutsk():
    assert Settings().tz.key == "Asia/Yakutsk"


def test_unknown_timezone_is_rejected():
    with pytest.raises(ValueError):
        Settings(timezone="Mars/Olympus")
