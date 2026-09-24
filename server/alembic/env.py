"""Alembic environment: runs migrations against shiftmate's configured engine (SQLite locally, PostgreSQL 16 on
the site server), or against `sqlalchemy.url` when a caller sets it (migration tests). `target_metadata` is the ORM
metadata so `alembic check` compares the schema with models.py."""

from sqlalchemy import create_engine

from alembic import context
from shiftmate import models  # noqa: F401  (registers every table on Base.metadata)
from shiftmate.db import Base, engine

target_metadata = Base.metadata
_url = context.config.get_main_option("sqlalchemy.url")
if _url:
    engine = create_engine(_url)


def run_migrations_offline() -> None:
    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=engine.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
