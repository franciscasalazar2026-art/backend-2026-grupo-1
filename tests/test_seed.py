from sqlalchemy import func, select

from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
    UsuarioORM,
)
from app.infrastructure.security import verify_password
from scripts.seed import seed_data


def test_seed_is_reproducible_and_creates_connected_rows(db_session):
    first = seed_data(db_session)
    second = seed_data(db_session)

    assert first == second
    assert first == {
        "usuarios": 2,
        "clientes": 2,
        "servicios": 2,
        "profesionales": 2,
        "profesional_servicios": 2,
        "reservas": 2,
        "citas": 2,
    }
    assert db_session.scalar(select(func.count(ClienteORM.id))) == 2
    assert db_session.scalar(select(func.count(ServicioORM.id))) == 2
    assert db_session.scalar(select(func.count(ProfesionalORM.id))) == 2
    assert db_session.scalar(select(func.count(ProfesionalServicioORM.id))) == 2
    assert db_session.scalar(select(func.count(ReservaORM.id))) == 2
    assert db_session.scalar(select(func.count(CitaORM.id))) == 2


def test_seed_creates_demo_users_with_secure_passwords(db_session):
    seed_data(db_session)

    admin = db_session.scalar(
        select(UsuarioORM).where(
            UsuarioORM.email == "admin.demo@example.test"
        )
    )
    cliente = db_session.scalar(
        select(UsuarioORM).where(
            UsuarioORM.email == "cliente.demo@example.test"
        )
    )

    assert admin is not None
    assert admin.rol == "admin"
    assert admin.activo is True
    assert admin.password_hash != "AdminDemo2026!"
    assert verify_password("AdminDemo2026!", admin.password_hash)

    assert cliente is not None
    assert cliente.rol == "cliente"
    assert cliente.activo is True
    assert cliente.password_hash != "ClienteDemo2026!"
    assert verify_password("ClienteDemo2026!", cliente.password_hash)

    seed_data(db_session)

    assert db_session.scalar(
        select(func.count(UsuarioORM.id))
    ) == 2
