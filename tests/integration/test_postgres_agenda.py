from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import delete, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    DetalleReservaORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)
from app.infrastructure.repositories.cita_repository import CitaRepository
from tests.support.postgres import migration_config


@pytest.fixture
def reserva_doble(postgres_session: Session) -> dict:
    cliente = ClienteORM(
        nombre="Cliente integración",
        email="agenda@example.test",
        telefono="912345678",
    )
    profesional = ProfesionalORM(
        nombre="Profesional integración",
        especialidad="Peluquería",
        email="profesional@example.test",
        telefono="987654321",
    )
    corte = ServicioORM(nombre="Corte", duracion_minutos=30, precio=Decimal("12000.00"))
    peinado = ServicioORM(
        nombre="Peinado", duracion_minutos=45, precio=Decimal("15500.50")
    )
    postgres_session.add_all([cliente, profesional, corte, peinado])
    postgres_session.flush()
    postgres_session.add_all(
        [
            ProfesionalServicioORM(profesional_id=profesional.id, servicio_id=corte.id),
            ProfesionalServicioORM(
                profesional_id=profesional.id, servicio_id=peinado.id
            ),
        ]
    )
    postgres_session.commit()
    return {
        "cliente_id": cliente.id,
        "fecha": date.today() + timedelta(days=4),
        "hora": time(10, tzinfo=timezone.utc),
        "motivo": "Corte y peinado",
        "servicios": [
            {"profesional_id": profesional.id, "servicio_id": corte.id},
            {"profesional_id": profesional.id, "servicio_id": peinado.id},
        ],
    }


def test_alembic_upgrade_builds_core_and_auth_tables(postgres_engine):
    expected_tables = {
        "alembic_version",
        "citas",
        "clientes",
        "detalle_reservas",
        "profesionales",
        "profesional_servicios",
        "refresh_tokens",
        "reservas",
        "servicios",
        "tokens_recuperacion_usados",
        "usuarios",
    }
    head = ScriptDirectory.from_config(migration_config()).get_current_head()

    with postgres_engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == head
        assert expected_tables <= set(inspect(connection).get_table_names())


def test_postgres_rejects_duplicate_client_email(postgres_session):
    email = "duplicado@example.test"
    postgres_session.add(
        ClienteORM(nombre="Primera cuenta", email=email, telefono="912345678")
    )
    postgres_session.commit()
    postgres_session.add(
        ClienteORM(nombre="Segunda cuenta", email=email, telefono="987654321")
    )

    with pytest.raises(IntegrityError) as violation:
        postgres_session.commit()
    assert violation.value.orig.pgcode == "23505"
    postgres_session.rollback()

    persisted = postgres_session.scalars(
        select(ClienteORM).where(ClienteORM.email == email)
    ).one()
    assert persisted.nombre == "Primera cuenta"


def test_postgres_rejects_a_reservation_with_no_customer(postgres_session):
    postgres_session.add(ReservaORM(cliente_id=999_999))

    with pytest.raises(IntegrityError) as violation:
        postgres_session.commit()
    assert violation.value.orig.pgcode == "23503"
    postgres_session.rollback()
    assert postgres_session.scalar(select(func.count()).select_from(ReservaORM)) == 0


def test_appointment_persists_ordered_details_and_database_cascades(
    postgres_engine, postgres_session, reserva_doble
):
    cita = CitaRepository(postgres_session).crear(reserva_doble)
    inicio = datetime.combine(reserva_doble["fecha"], reserva_doble["hora"])

    # An independent session proves that the repository committed the entire graph.
    with Session(postgres_engine) as verification:
        persisted = verification.get(CitaORM, cita.id)
        assert persisted.fecha_hora == inicio
        assert persisted.reserva.cliente_id == reserva_doble["cliente_id"]

        detalles = sorted(persisted.reserva.detalles, key=lambda d: d.fecha_hora_inicio)
        assert [d.profesional_servicio.servicio_id for d in detalles] == [
            item["servicio_id"] for item in reserva_doble["servicios"]
        ]
        assert [d.fecha_hora_inicio for d in detalles] == [
            inicio,
            inicio + timedelta(minutes=30),
        ]
        assert [d.duracion_minutos for d in detalles] == [30, 45]
        assert [d.precio for d in detalles] == [
            Decimal("12000.00"),
            Decimal("15500.50"),
        ]

        # Execute a direct DELETE, so any cascade observed belongs to PostgreSQL.
        verification.execute(
            delete(ReservaORM).where(ReservaORM.id == persisted.reserva_id)
        )
        verification.commit()

    with Session(postgres_engine) as verification:
        assert verification.get(CitaORM, cita.id) is None
        assert (
            verification.scalar(select(func.count()).select_from(DetalleReservaORM))
            == 0
        )
        assert verification.get(ClienteORM, reserva_doble["cliente_id"]) is not None


def test_pg_not_null_violation_rolls_back_reservation_and_details(
    postgres_engine, postgres_session, reserva_doble
):
    repositorio = CitaRepository(postgres_session)

    # Bypass DTO validation to trigger a real write failure after the reserva flush.
    with pytest.raises(RuntimeError, match="Conflicto al registrar la cita") as failure:
        repositorio.crear({**reserva_doble, "motivo": None})

    assert isinstance(failure.value.__cause__, IntegrityError)
    assert failure.value.__cause__.orig.pgcode == "23502"
    with Session(postgres_engine) as verification:
        for model in (ReservaORM, CitaORM, DetalleReservaORM):
            assert verification.scalar(select(func.count()).select_from(model)) == 0

    recovered = repositorio.crear(reserva_doble)
    assert len(recovered.servicios) == 2
