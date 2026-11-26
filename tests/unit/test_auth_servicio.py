from datetime import datetime, timedelta, timezone
from unittest.mock import create_autospec, patch

import pytest

from app.application.services import auth_servicio
from app.application.services.auth_servicio import AuthError, AuthServicio
from app.infrastructure.models.usuario import UsuarioORM
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.security import (
    create_access_token,
    decode_and_validate_token,
    hash_password,
    hash_token,
    verify_password,
)


@pytest.fixture
def repo():
    return create_autospec(UsuarioRepository, instance=True, spec_set=True)


@pytest.fixture
def usuario():
    return UsuarioORM(
        id=17,
        nombre="Cuenta de prueba",
        email="cuenta@example.com",
        rol="cliente",
        activo=True,
        password_hash=hash_password("Clave larga inicial"),
        intentos_fallidos=0,
        token_version=2,
    )


def test_register_assigns_base_role_and_stores_only_hash(repo):
    repo.obtener_por_email.return_value = None
    password = "Clave nueva fuerte"

    AuthServicio(repo).registrar_usuario("Cuenta nueva", "nueva@example.com", password)

    fields = repo.crear_usuario.call_args.kwargs
    assert fields["email"] == "nueva@example.com"
    assert fields["rol"] == "cliente"
    assert fields["password_hash"] != password
    assert verify_password(password, fields["password_hash"])


def test_register_rejects_short_password_before_persistence(repo):
    with pytest.raises(AuthError) as error:
        AuthServicio(repo).registrar_usuario(
            "Cuenta débil", "debil@example.com", "corta"
        )

    assert error.value.status_code == 422
    repo.crear_usuario.assert_not_called()


def test_register_duplicate_email_leaves_existing_user(repo, usuario):
    repo.obtener_por_email.return_value = usuario

    with pytest.raises(AuthError) as error:
        AuthServicio(repo).registrar_usuario(
            usuario.nombre, usuario.email, "Clave larga inicial"
        )

    assert error.value.status_code == 409
    repo.crear_usuario.assert_not_called()


def test_login_unknown_email_and_incorrect_password_return_same_error(repo, usuario):
    repo.obtener_por_email.side_effect = [None, usuario]
    auth = AuthServicio(repo)

    with pytest.raises(AuthError) as unknown:
        auth.iniciar_sesion("desconocido@example.com", "Clave inexistente")
    with pytest.raises(AuthError) as incorrect:
        auth.iniciar_sesion(usuario.email, "Clave incorrecta")

    assert unknown.value.status_code == incorrect.value.status_code == 401
    assert str(unknown.value) == str(incorrect.value)
    assert usuario.intentos_fallidos == 1
    repo.guardar_refresh_token.assert_not_called()


def test_login_temporarily_locked_user_cannot_get_tokens(repo, usuario):
    usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(hours=1)
    repo.obtener_por_email.return_value = usuario

    with pytest.raises(AuthError) as error:
        AuthServicio(repo).iniciar_sesion(usuario.email, "Clave larga inicial")

    assert error.value.status_code == 429
    repo.guardar_refresh_token.assert_not_called()


def test_fifth_failed_login_locks_for_fifteen_minutes_and_rejects_correct_password(
    repo, usuario
):
    instant = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    repo.obtener_por_email.return_value = usuario
    auth = AuthServicio(repo)

    with patch.object(auth_servicio, "datetime", wraps=datetime) as clock:
        clock.now.return_value = instant
        for attempt in range(1, 6):
            with pytest.raises(AuthError) as incorrect:
                auth.iniciar_sesion(usuario.email, "Contraseña incorrecta")

            assert incorrect.value.status_code == 401
            assert usuario.intentos_fallidos == attempt
            assert repo.actualizar_usuario.call_count == attempt
            repo.actualizar_usuario.assert_called_with(usuario)
            if attempt < 5:
                assert usuario.bloqueado_hasta is None

        assert usuario.bloqueado_hasta == instant + timedelta(minutes=15)
        with pytest.raises(AuthError) as locked:
            auth.iniciar_sesion(usuario.email, "Clave larga inicial")

    assert locked.value.status_code == 429
    assert usuario.intentos_fallidos == 5
    assert repo.actualizar_usuario.call_count == 5
    repo.guardar_refresh_token.assert_not_called()


def test_successful_login_after_expired_lock_clears_lock_and_failed_attempts(
    repo, usuario
):
    instant = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    usuario.intentos_fallidos = 5
    usuario.bloqueado_hasta = instant - timedelta(seconds=1)
    repo.obtener_por_email.return_value = usuario

    with patch.object(auth_servicio, "datetime", wraps=datetime) as clock:
        clock.now.return_value = instant
        tokens = AuthServicio(repo).iniciar_sesion(usuario.email, "Clave larga inicial")

    assert tokens["usuario"] is usuario
    assert tokens["access_token"] and tokens["refresh_token"]
    assert usuario.intentos_fallidos == 0
    assert usuario.bloqueado_hasta is None
    repo.actualizar_usuario.assert_called_once_with(usuario)
    repo.guardar_refresh_token.assert_called_once()


def test_inactive_user_cannot_login_even_with_correct_password(repo, usuario):
    instant = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    usuario.activo = False
    repo.obtener_por_email.return_value = usuario

    with patch.object(auth_servicio, "datetime", wraps=datetime) as clock:
        clock.now.return_value = instant
        with pytest.raises(AuthError) as error:
            AuthServicio(repo).iniciar_sesion(usuario.email, "Clave larga inicial")

    assert error.value.status_code == 401
    repo.actualizar_usuario.assert_called_once_with(usuario)
    repo.guardar_refresh_token.assert_not_called()


def test_successful_login_clears_failed_attempts_and_stores_refresh_hash(repo, usuario):
    usuario.intentos_fallidos = 2
    repo.obtener_por_email.return_value = usuario

    tokens = AuthServicio(repo).iniciar_sesion(usuario.email, "Clave larga inicial")

    claims = decode_and_validate_token(tokens["access_token"], expected_type="access")
    fields = repo.guardar_refresh_token.call_args.kwargs
    assert claims["sub"] == str(usuario.id)
    assert claims["ver"] == usuario.token_version
    assert fields["usuario_id"] == usuario.id
    assert fields["token_hash"] == hash_token(tokens["refresh_token"])
    assert fields["token_hash"] != tokens["refresh_token"]
    assert usuario.intentos_fallidos == 0
    repo.actualizar_usuario.assert_called_once_with(usuario)


def test_reset_rejects_access_token_before_querying_user(repo, usuario):
    access = create_access_token(subject=usuario.id, role=usuario.rol)

    with pytest.raises(AuthError) as error:
        AuthServicio(repo).restablecer_contrasena(access, "Otra clave larga")

    assert error.value.status_code == 401
    repo.consumir_recuperacion.assert_not_called()
