import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.domain.rules.politica_contrasena import validar_politica_contrasena
from app.infrastructure.models.usuario import UsuarioORM
from app.infrastructure.security import (
    create_access_token,
    create_recovery_token,
    decode_and_validate_token,
    generate_opaque_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.presentation.dependencies import require_role


def test_password_policy_accepts_exact_minimum():
    validar_politica_contrasena("123456789012")


@pytest.mark.parametrize("password", ["", "12345678901"])
def test_password_policy_rejects_password_under_minimum(password):
    with pytest.raises(ValueError, match="12 caracteres"):
        validar_politica_contrasena(password)


def test_password_hash_verifies_only_original_password():
    password = "Clave de prueba 2026"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("Otra clave distinta", hashed)


def test_valid_access_token_keeps_identity_role_and_version():
    token = create_access_token(subject=37, role="recepcionista", token_version=4)

    claims = decode_and_validate_token(token, expected_type="access")

    assert claims["sub"] == "37"
    assert claims["role"] == "recepcionista"
    assert claims["ver"] == 4
    assert claims["exp"] > claims["iat"]


def test_expired_access_token_is_rejected_without_waiting():
    token = create_access_token(
        subject=1,
        role="cliente",
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(ValueError, match="inválido o expirado"):
        decode_and_validate_token(token, expected_type="access")


def test_tampered_payload_cannot_escalate_role():
    token = create_access_token(subject=1, role="cliente")
    header, payload, signature = token.split(".")
    claims = json.loads(urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["role"] = "admin"
    tampered_payload = (
        urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    )

    with pytest.raises(ValueError, match="inválido o expirado"):
        decode_and_validate_token(
            f"{header}.{tampered_payload}.{signature}", expected_type="access"
        )


def test_recovery_and_access_tokens_cannot_be_interchanged():
    access = create_access_token(subject=2, role="cliente")
    recovery, jti, expires_at = create_recovery_token(subject=2)
    recovery_claims = decode_and_validate_token(recovery, expected_type="recovery")

    assert recovery_claims["sub"] == "2"
    assert recovery_claims["jti"] == jti
    assert recovery_claims["exp"] == int(expires_at.timestamp())
    with pytest.raises(ValueError, match="Propósito"):
        decode_and_validate_token(access, expected_type="recovery")
    with pytest.raises(ValueError, match="Propósito"):
        decode_and_validate_token(recovery, expected_type="access")


def test_refresh_token_persists_only_a_hash_and_has_a_future_expiry():
    raw, hashed, expires_at = generate_opaque_refresh_token()
    another_raw, _, _ = generate_opaque_refresh_token()

    assert raw != another_raw
    assert raw != hashed
    assert hash_token(raw) == hashed
    assert expires_at > datetime.now(timezone.utc)


def test_role_guard_allows_receptionist_for_shared_operation():
    usuario = UsuarioORM(rol="recepcionista")

    assert require_role("admin", "recepcionista")(usuario) is usuario


def test_role_guard_rejects_authenticated_client_for_privileged_operation():
    with pytest.raises(HTTPException) as error:
        require_role("admin", "recepcionista")(UsuarioORM(rol="cliente"))

    assert error.value.status_code == 403
