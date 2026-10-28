"""Shared isolated database and API fixtures for backend tests."""

import os
from collections.abc import Iterator

# The application validates its PostgreSQL settings when the database module
# is imported. Test requests replace that dependency with an in-memory SQLite
# database, so these values are placeholders and never open a PostgreSQL link.
for key, value in {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "5432",
    "DB_NAME": "backend_tests",
    "DB_USER": "backend_tests",
    "DB_PASSWORD": "backend_tests",
}.items():
    os.environ.setdefault(key, value)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database import Base, get_db
from app.infrastructure.models import (  # noqa: F401
    CitaORM,
    ClienteORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)
from app.main import app


@pytest.fixture
def db_engine() -> Iterator:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Iterator[Session]:
    test_sessions = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    with test_sessions() as db:
        yield db


@pytest.fixture
def client(db_engine) -> Iterator[TestClient]:
    test_sessions = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db() -> Iterator[Session]:
        with test_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def agenda_ids(db_session: Session) -> dict[str, int]:
    """Create the minimum connected records required by appointment routes."""
    cliente = ClienteORM(
        nombre="Cliente de prueba",
        email="cliente.pruebas@example.test",
        telefono="912345678",
        activo=True,
    )
    servicio = ServicioORM(
        nombre="Corte de prueba",
        descripcion="Servicio para pruebas",
        duracion_minutos=45,
        precio="12000.00",
        activo=True,
    )
    profesional = ProfesionalORM(
        nombre="Profesional de prueba",
        especialidad="Peluquería",
        email="profesional.pruebas@example.test",
        telefono="987654321",
        activo=True,
    )
    db_session.add_all([cliente, servicio, profesional])
    db_session.flush()

    asignacion = ProfesionalServicioORM(
        profesional_id=profesional.id,
        servicio_id=servicio.id,
    )
    db_session.add(asignacion)
    db_session.commit()

    return {
        "cliente_id": cliente.id,
        "servicio_id": servicio.id,
        "profesional_id": profesional.id,
        "asignacion_id": asignacion.id,
    }
