import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "cambia-este-secreto-en-produccion-min-32-chars"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
RECOVERY_TOKEN_EXPIRE_MINUTES = int(os.getenv("RECOVERY_TOKEN_EXPIRE_MINUTES", "10"))

password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    # Genera un hash Argon2id seguro a partir de una contraseña en texto plano
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verifica que una contraseña en texto plano coincida con un hash Argon2id almacenado
    return password_hasher.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    # Genera un hash SHA-256 seguro a partir de un token opaco
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str | int,
    role: str,
    token_version: int = 1,
    expires_delta: timedelta | None = None,
) -> str:
    # Emite un Access JWT firmado con expiración corta y propósito 'access'
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "ver": token_version,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_recovery_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    *,
    token_version: int = 1,
) -> tuple[str, str, datetime]:
    # Emite un Recovery JWT firmado con expiración corta y propósito 'recovery', devolviendo el token, su jti y fecha de expiración
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=RECOVERY_TOKEN_EXPIRE_MINUTES))
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": str(subject),
        "jti": jti,
        "ver": token_version,
        "type": "recovery",
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, jti, expire


def decode_and_validate_token(token: str, expected_type: str) -> dict[str, Any]:
    # Decodifica un JWT y valida su propósito y expiración, lanzando ValueError si es inválido
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("Token inválido o expirado") from exc

    if payload.get("type") != expected_type:
        raise ValueError(f"Propósito de token inválido: se esperaba '{expected_type}'")

    return payload


def generate_opaque_refresh_token() -> tuple[str, str, datetime]:
    # Genera un token de refresco opaco seguro, su hash y fecha de expiración
    raw_token = secrets.token_urlsafe(48)
    hashed = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, hashed, expires_at
