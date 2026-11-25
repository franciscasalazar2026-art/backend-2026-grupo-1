from datetime import datetime, timedelta, timezone

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
from app.infrastructure.security import hash_password, verify_password
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


def test_seed_updates_legacy_demo_emails_preserving_identity_and_security_state(db_session):
    anteriores = [
        UsuarioORM(
            nombre="Nombre modificado del antiguo administrador",
            email="admin.demo@example.test",
            password_hash=hash_password("Clave anterior cambiada admin"),
            rol="cliente",
            activo=False,
            token_version=7,
            intentos_fallidos=3,
            bloqueado_hasta=datetime.now(timezone.utc) + timedelta(minutes=10),
        ),
        UsuarioORM(
            nombre="Nombre modificado del antiguo cliente",
            email="cliente.demo@example.test",
            password_hash=hash_password("Clave anterior cambiada cliente"),
            rol="recepcionista",
            activo=True,
            token_version=4,
            intentos_fallidos=2,
        ),
    ]
    db_session.add_all(anteriores)
    db_session.commit()
    campos_preservados = (
        "id", "nombre", "password_hash", "rol", "activo", "token_version",
        "intentos_fallidos", "bloqueado_hasta",
    )
    estado_anterior = {
        cuenta.id: {campo: getattr(cuenta, campo) for campo in campos_preservados}
        for cuenta in anteriores
    }
    correos_esperados = {
        anteriores[0].id: "admin.demo@example.com",
        anteriores[1].id: "cliente.demo@example.com",
    }

    for _ in range(2):
        seed_data(db_session)
        db_session.expire_all()
        cuentas = list(db_session.scalars(select(UsuarioORM)))
        assert {cuenta.id: cuenta.email for cuenta in cuentas} == correos_esperados
        assert {
            cuenta.id: {campo: getattr(cuenta, campo) for campo in campos_preservados}
            for cuenta in cuentas
        } == estado_anterior

    assert verify_password("Clave anterior cambiada admin", anteriores[0].password_hash)
    assert verify_password("Clave anterior cambiada cliente", anteriores[1].password_hash)


def test_seed_does_not_merge_legacy_account_when_current_demo_email_is_taken(db_session):
    actuales = [
        UsuarioORM(
            nombre="Cuenta anterior de demostración",
            email="admin.demo@example.test",
            password_hash=hash_password("Clave conservada anterior"),
            rol="recepcionista",
            activo=False,
            token_version=6,
            intentos_fallidos=2,
        ),
        UsuarioORM(
            nombre="Otra cuenta que ya usa el correo actual",
            email="admin.demo@example.com",
            password_hash=hash_password("Clave conservada de otra cuenta"),
            rol="cliente",
            activo=True,
            token_version=3,
            intentos_fallidos=1,
        ),
    ]
    db_session.add_all(actuales)
    db_session.commit()
    campos_preservados = (
        "id", "nombre", "email", "password_hash", "rol", "activo", "token_version",
        "intentos_fallidos", "bloqueado_hasta",
    )
    estado_anterior = {
        cuenta.id: {campo: getattr(cuenta, campo) for campo in campos_preservados}
        for cuenta in actuales
    }

    for _ in range(2):
        seed_data(db_session)
        db_session.expire_all()
        for cuenta in actuales:
            assert {
                campo: getattr(cuenta, campo) for campo in campos_preservados
            } == estado_anterior[cuenta.id]
        assert db_session.scalar(select(func.count(UsuarioORM.id))) == 3

    assert verify_password("Clave conservada anterior", actuales[0].password_hash)
    assert verify_password("Clave conservada de otra cuenta", actuales[1].password_hash)
