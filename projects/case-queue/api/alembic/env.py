from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Substitute %(DATABASE_URL)s in alembic.ini from environment
database_url = os.environ.get("DATABASE_URL", "")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(cfg, prefix="sqlalchemy.", poolclass=NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
