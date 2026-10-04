from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migrations_create_all_tables(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrations.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "head")

    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"users", "subjects", "excuse_templates", "excuse_history"} <= tables
