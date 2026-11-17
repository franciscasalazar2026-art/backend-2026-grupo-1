"""Alembic-backed fixtures for an explicitly selected local PostgreSQL DB."""

import os
import re
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[2]
TEST_POSTGRES_URL = "TEST_POSTGRES_URL"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
TEST_DATABASE_NAME = re.compile(
    r"(?:test_[a-z0-9_]+|[a-z0-9_]+_tests?(?:_[a-z0-9_]+)?)"
)


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(ROOT / "migrations"))
    return config


def _test_database_url() -> URL:
    value = os.getenv(TEST_POSTGRES_URL)
    if not value:
        pytest.skip(f"Define {TEST_POSTGRES_URL} to run PostgreSQL tests.")

    try:
        url = make_url(value)
    except (ArgumentError, ValueError):
        pytest.fail(
            f"{TEST_POSTGRES_URL} is not a valid SQLAlchemy URL.", pytrace=False
        )

    if (
        url.drivername not in {"postgresql", "postgresql+psycopg2"}
        or url.host not in LOCAL_HOSTS
        or not url.port
        or not url.username
        or not url.password
        or not TEST_DATABASE_NAME.fullmatch(url.database or "")
        or url.query
    ):
        pytest.fail(
            f"{TEST_POSTGRES_URL} must point to a loopback PostgreSQL instance with "
            "an explicit port, credentials, and a test database name "
            "(test_*, *_test, *_tests or *_test_*). Leave URL query options empty.",
            pytrace=False,
        )
    return url.set(drivername="postgresql+psycopg2")


@pytest.fixture
def postgres_engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """Run actual migrations in a fresh, uniquely named schema for each test."""
    url = _test_database_url()
    schema = f"test_{uuid4().hex}"
    search_path = f"-c search_path={schema}"
    # Explicit hostaddr keeps an ambient libpq PGHOSTADDR from rerouting the connection.
    hostaddr = "127.0.0.1" if url.host == "localhost" else url.host
    connection_args = {"hostaddr": hostaddr, "connect_timeout": 5}
    admin = create_engine(url, poolclass=NullPool, connect_args=connection_args)
    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args={
            **connection_args,
            "options": f"{search_path} -c statement_timeout=15000",
        },
    )

    try:
        with admin.begin() as connection:
            connection.execute(text(f"CREATE SCHEMA {schema}"))

        try:
            # migrations/env.py builds its own URL from these variables.
            with monkeypatch.context() as environment:
                environment.setenv("DB_HOST", url.host)
                environment.setenv("DB_PORT", str(url.port))
                environment.setenv("DB_NAME", url.database)
                environment.setenv("DB_USER", url.username)
                environment.setenv("DB_PASSWORD", url.password)
                environment.setenv("PGHOSTADDR", hostaddr)
                environment.setenv("PGOPTIONS", search_path)
                command.upgrade(migration_config(), "head")

            with engine.connect() as connection:
                assert connection.scalar(text("SELECT current_schema()")) == schema
            yield engine
        finally:
            engine.dispose()
            with admin.begin() as connection:
                connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
    finally:
        admin.dispose()


@pytest.fixture
def postgres_session(postgres_engine: Engine) -> Iterator[Session]:
    with Session(postgres_engine) as session:
        yield session
