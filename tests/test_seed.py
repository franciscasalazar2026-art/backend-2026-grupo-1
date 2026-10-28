from sqlalchemy import func, select

from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)
from scripts.seed import seed_data


def test_seed_is_reproducible_and_creates_connected_rows(db_session):
    first = seed_data(db_session)
    second = seed_data(db_session)

    assert first == second
    assert first == {
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
