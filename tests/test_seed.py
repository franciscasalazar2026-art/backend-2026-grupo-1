import pytest
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
        "reservas": 3,
        "citas": 3,
    }
    assert db_session.scalar(select(func.count(ClienteORM.id))) == 2
    assert db_session.scalar(select(func.count(ServicioORM.id))) == 2
    assert db_session.scalar(select(func.count(ProfesionalORM.id))) == 2
    assert db_session.scalar(select(func.count(ProfesionalServicioORM.id))) == 2
    assert db_session.scalar(select(func.count(ReservaORM.id))) == 3
    cliente_uno = db_session.scalar(
        select(ClienteORM).where(
            ClienteORM.email == "seed.cliente1@example.test"
        )
    )
    assert cliente_uno is not None
    assert db_session.scalar(
        select(func.count(ReservaORM.id)).where(
            ReservaORM.cliente_id == cliente_uno.id
        )
    ) == 2
    assert db_session.scalar(select(func.count(CitaORM.id))) == 3


def test_seed_creates_demo_users_with_secure_passwords(db_session):
    seed_data(db_session)

    admin = db_session.scalar(
        select(UsuarioORM).where(
            UsuarioORM.email == "admin.demo@example.com"
        )
    )
    cliente = db_session.scalar(
        select(UsuarioORM).where(
            UsuarioORM.email == "cliente.demo@example.com"
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


@pytest.mark.parametrize(
    "email,password,rol",
    [
        ("admin.demo@example.com", "AdminDemo2026!", "admin"),
        ("cliente.demo@example.com", "ClienteDemo2026!", "cliente"),
    ],
)
def test_seed_demo_accounts_can_login_through_http(
    client, db_session, email, password, rol
):
    seed_data(db_session)

    respuesta = client.post("/auth/login", json={"email": email, "password": password})
    assert respuesta.status_code == 200
    sesion = respuesta.json()
    assert sesion["token_type"] == "bearer"
    assert sesion["access_token"] and sesion["refresh_token"]
    usuario = sesion["usuario"]
    assert set(usuario) == {"id", "nombre", "email", "rol", "activo"}
    assert usuario["email"] == email
    assert usuario["rol"] == rol
    assert usuario["activo"] is True

    perfil = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {sesion['access_token']}"}
    )
    assert perfil.status_code == 200
    assert perfil.json() == usuario

    credencial_incorrecta = client.post(
        "/auth/login",
        json={"email": email, "password": "Clave incorrecta de prueba"},
    )
    assert credencial_incorrecta.status_code == 401
    error = credencial_incorrecta.json()
    assert set(error) == {"error", "mensaje", "detail"}
    assert error["error"] == "HTTP_401"
