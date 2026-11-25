from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.services.auth_servicio import AuthError, AuthServicio
from app.infrastructure.models import (
    RefreshTokenORM,
    TokenRecuperacionUsadoORM,
    UsuarioORM,
)
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.security import (
    create_recovery_token,
    hash_password,
    hash_token,
    verify_password,
)

EMAIL = "cuenta.integracion@example.test"
INITIAL_PASSWORD = "Inicial-Prueba-2026!"
NEW_PASSWORD = "Cambio-Prueba-2026!"


@pytest.fixture
def auth_service(postgres_session: Session) -> AuthServicio:
    servicio = AuthServicio(UsuarioRepository(postgres_session))
    servicio.registrar_usuario("Cuenta de integración", EMAIL, INITIAL_PASSWORD)
    return servicio


def test_real_refresh_rotation_persists_hash_and_family(auth_service, postgres_engine):
    first = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    renewed = auth_service.renovar_tokens(first["refresh_token"])
    assert renewed["refresh_token"] != first["refresh_token"]
    assert renewed["token_type"] == "bearer"

    with Session(postgres_engine) as verification:
        by_hash = {
            record.token_hash: record
            for record in verification.scalars(select(RefreshTokenORM))
        }
        assert set(by_hash) == {
            hash_token(first["refresh_token"]),
            hash_token(renewed["refresh_token"]),
        }
        old = by_hash[hash_token(first["refresh_token"])]
        new = by_hash[hash_token(renewed["refresh_token"])]
        assert old.familia_id == new.familia_id
        assert old.revocado and not new.revocado
        assert new.expira_en > datetime.now(timezone.utc)


def test_reusing_refresh_revokes_its_family_only(auth_service, postgres_engine):
    first = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    other = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    renewed = auth_service.renovar_tokens(first["refresh_token"])

    with pytest.raises(AuthError, match="Reutilización") as replay:
        auth_service.renovar_tokens(first["refresh_token"])
    assert replay.value.status_code == 401

    with Session(postgres_engine) as verification:
        by_hash = {
            record.token_hash: record
            for record in verification.scalars(select(RefreshTokenORM))
        }
        assert by_hash[hash_token(first["refresh_token"])].revocado
        assert by_hash[hash_token(renewed["refresh_token"])].revocado
        assert not by_hash[hash_token(other["refresh_token"])].revocado

    with pytest.raises(AuthError) as revoked:
        auth_service.renovar_tokens(renewed["refresh_token"])
    assert revoked.value.status_code == 401
    assert auth_service.renovar_tokens(other["refresh_token"])["refresh_token"]


def test_expired_refresh_is_rejected_and_revoked(
    auth_service, postgres_session, postgres_engine
):
    login = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    token_hash = hash_token(login["refresh_token"])
    query = select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
    persisted = postgres_session.scalars(query).one()
    persisted.expira_en = datetime.now(timezone.utc) - timedelta(seconds=1)
    postgres_session.commit()

    with pytest.raises(AuthError, match="expirado") as expired:
        auth_service.renovar_tokens(login["refresh_token"])
    assert expired.value.status_code == 401

    with Session(postgres_engine) as verification:
        assert verification.scalars(query).one().revocado


def test_reset_consumes_jti_and_revokes_all_refresh_sessions(
    auth_service, postgres_engine
):
    first = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    second = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    user_id = first["usuario"].id
    token, jti, _ = create_recovery_token(user_id)

    with Session(postgres_engine) as request:
        AuthServicio(UsuarioRepository(request)).restablecer_contrasena(
            token, NEW_PASSWORD
        )
    with Session(postgres_engine) as request, pytest.raises(AuthError) as reused:
        AuthServicio(UsuarioRepository(request)).restablecer_contrasena(
            token, "Otro-Cambio-Prueba-2026!"
        )
    assert reused.value.status_code == 400

    with Session(postgres_engine) as verification:
        persisted = verification.get(UsuarioORM, user_id)
        assert persisted.token_version == 2
        assert verify_password(NEW_PASSWORD, persisted.password_hash)
        assert not verify_password(INITIAL_PASSWORD, persisted.password_hash)
        consumed = verification.scalars(select(TokenRecuperacionUsadoORM)).one()
        assert (consumed.jti, consumed.usuario_id) == (jti, user_id)
        sessions = list(verification.scalars(select(RefreshTokenORM)))
        assert {row.token_hash for row in sessions} == {
            hash_token(first["refresh_token"]),
            hash_token(second["refresh_token"]),
        }
        assert all(row.revocado for row in sessions)


def test_concurrent_reset_accepts_only_one_password(auth_service, postgres_engine):
    user_id = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)["usuario"].id
    token, jti, _ = create_recovery_token(user_id)
    simultaneas = Barrier(2)

    def reset_candidate(candidate: str) -> tuple[int, str]:
        with Session(postgres_engine) as session:
            servicio = AuthServicio(UsuarioRepository(session))
            simultaneas.wait(timeout=10)
            try:
                servicio.restablecer_contrasena(token, candidate)
            except AuthError as error:
                return error.status_code, candidate
            return 200, candidate

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = list(
            executor.map(
                reset_candidate,
                ("Candidato-Uno-2026!", "Candidato-Dos-2026!"),
                timeout=35,
            )
        )

    assert sorted(status for status, _ in attempts) == [200, 400]
    winner = next(candidate for status, candidate in attempts if status == 200)
    rejected = next(candidate for status, candidate in attempts if status == 400)

    with Session(postgres_engine) as verification:
        persisted = verification.get(UsuarioORM, user_id)
        assert persisted.token_version == 2
        assert verify_password(winner, persisted.password_hash)
        assert not verify_password(rejected, persisted.password_hash)
        assert verification.scalars(select(TokenRecuperacionUsadoORM)).one().jti == jti


def test_reset_failure_rolls_back_password_consumption_and_revocation(
    auth_service, postgres_engine, postgres_session
):
    login = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    user_id = login["usuario"].id
    postgres_session.rollback()  # Release read locks before changing the test schema.
    token, jti, _ = create_recovery_token(user_id)

    # Force the actual PostgreSQL write to fail inside the recovery transaction.
    with postgres_engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE refresh_tokens ADD CONSTRAINT test_refresh_write_failure "
                "CHECK (revocado IS FALSE)"
            )
        )

    with Session(postgres_engine) as request, pytest.raises(IntegrityError) as failure:
        AuthServicio(UsuarioRepository(request)).restablecer_contrasena(
            token, NEW_PASSWORD
        )
    assert failure.value.orig.pgcode == "23514"

    with Session(postgres_engine) as verification:
        persisted = verification.get(UsuarioORM, user_id)
        assert persisted.token_version == 1
        assert verify_password(INITIAL_PASSWORD, persisted.password_hash)
        assert verification.scalars(select(TokenRecuperacionUsadoORM)).first() is None
        assert not verification.scalars(select(RefreshTokenORM)).one().revocado

    with postgres_engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE refresh_tokens DROP CONSTRAINT test_refresh_write_failure"
            )
        )
    with Session(postgres_engine) as request:
        AuthServicio(UsuarioRepository(request)).restablecer_contrasena(
            token, NEW_PASSWORD
        )
    with Session(postgres_engine) as verification:
        assert verification.scalars(select(TokenRecuperacionUsadoORM)).one().jti == jti
        assert verification.scalars(select(RefreshTokenORM)).one().revocado


def test_login_lock_survives_a_new_database_session(auth_service, postgres_engine):
    for _ in range(5):
        with pytest.raises(AuthError) as failure:
            auth_service.iniciar_sesion(EMAIL, "Clave-Incorrecta-2026!")
        assert failure.value.status_code == 401

    with Session(postgres_engine) as verification:
        user = verification.scalars(select(UsuarioORM)).one()
        assert user.intentos_fallidos == 5
        assert user.bloqueado_hasta > datetime.now(timezone.utc)
        assert verification.scalars(select(RefreshTokenORM)).first() is None

    # A different request must read and enforce the lock persisted by the failures.
    with Session(postgres_engine) as request, pytest.raises(AuthError) as locked:
        AuthServicio(UsuarioRepository(request)).iniciar_sesion(EMAIL, INITIAL_PASSWORD)
    assert locked.value.status_code == 429

    with Session(postgres_engine) as verification:
        assert verification.scalars(select(UsuarioORM)).one().intentos_fallidos == 5
        assert verification.scalars(select(RefreshTokenORM)).first() is None


def test_user_email_is_normalized_and_unique_in_postgresql(
    postgres_session, postgres_engine
):
    repository = UsuarioRepository(postgres_session)
    password_hash = hash_password(INITIAL_PASSWORD)
    first = repository.crear_usuario(
        nombre="  Cuenta normalizada  ",
        email="  Mi.Cuenta@Example.COM  ",
        password_hash=password_hash,
    )
    first_id = first.id
    assert first.nombre == "Cuenta normalizada"
    assert first.email == "mi.cuenta@example.com"

    with pytest.raises(IntegrityError) as duplicate:
        repository.crear_usuario(
            nombre="Otra cuenta",
            email="MI.CUENTA@example.com",
            password_hash=password_hash,
        )
    assert duplicate.value.orig.pgcode == "23505"
    postgres_session.rollback()

    with Session(postgres_engine) as verification:
        persisted = verification.scalars(select(UsuarioORM)).one()
        assert persisted.id == first_id
        assert persisted.nombre == "Cuenta normalizada"
        assert persisted.email == "mi.cuenta@example.com"
        assert verify_password(INITIAL_PASSWORD, persisted.password_hash)


def test_concurrent_distinct_recovery_tokens_allow_only_one_change(
    auth_service, postgres_engine
):
    user_id = auth_service.iniciar_sesion(EMAIL, INITIAL_PASSWORD)["usuario"].id
    first, first_jti, _ = create_recovery_token(user_id)
    second, second_jti, _ = create_recovery_token(user_id)
    assert first_jti != second_jti
    simultaneous = Barrier(2)

    def attempt(candidate: tuple[str, str]) -> tuple[int, str, str]:
        token, password = candidate
        with Session(postgres_engine) as session:
            service = AuthServicio(UsuarioRepository(session))
            simultaneous.wait(timeout=10)
            try:
                service.restablecer_contrasena(token, password)
            except AuthError as error:
                return error.status_code, token, password
            return 200, token, password

    candidates = (
        (first, "Primer-Candidato-2026!"),
        (second, "Segundo-Candidato-2026!"),
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(attempt, candidates, timeout=35))

    assert sorted(status for status, _, _ in outcomes) == [200, 401]
    _, winning_token, winning_password = next(row for row in outcomes if row[0] == 200)
    _, _, rejected_password = next(row for row in outcomes if row[0] == 401)
    winning_jti = first_jti if winning_token == first else second_jti
    with Session(postgres_engine) as verification:
        user = verification.get(UsuarioORM, user_id)
        assert user.token_version == 2
        assert verify_password(winning_password, user.password_hash)
        assert not verify_password(rejected_password, user.password_hash)
        assert (
            verification.scalars(select(TokenRecuperacionUsadoORM)).one().jti
            == winning_jti
        )
        assert all(
            row.revocado for row in verification.scalars(select(RefreshTokenORM))
        )
