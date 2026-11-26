"""Start the API as a separate process with an Alembic-migrated PostgreSQL schema."""

import os
import re
import secrets
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from uuid import uuid4

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.models.usuario import UsuarioORM
from app.infrastructure.security import hash_password
from tests.support.postgres import postgres_engine as postgres_engine

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ServidorE2E:
    http: httpx2.Client
    buzon: Path
    jwt_secret: str


def _esperar_url(proceso: subprocess.Popen, log: Path) -> str:
    try:
        espera = float(os.getenv("E2E_STARTUP_TIMEOUT", "60"))
    except ValueError:
        pytest.fail(
            "E2E_STARTUP_TIMEOUT debe ser un número mayor que 0 y hasta 300 segundos.",
            pytrace=False,
        )
    if not 0 < espera <= 300:
        pytest.fail(
            "E2E_STARTUP_TIMEOUT debe ser un número mayor que 0 y hasta 300 segundos.",
            pytrace=False,
        )
    plazo = monotonic() + espera
    while monotonic() < plazo:
        if proceso.poll() is not None:
            pytest.fail(f"Uvicorn terminó con código {proceso.returncode}. Log: {log}")
        salida = log.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Uvicorn running on (http://127\.0\.0\.1:\d+)", salida)
        if match:
            return match.group(1)
        sleep(0.05)
    pytest.fail(
        f"Uvicorn no abrió un puerto local en {espera:g} segundos. Log: {log}"
    )


@pytest.fixture
def servidor_e2e(postgres_engine, tmp_path) -> Iterator[ServidorE2E]:
    with postgres_engine.connect() as conexion:
        esquema = conexion.scalar(text("SELECT current_schema()"))
    # El esquema debe ser el desechable que preparó la fixture, nunca public.
    assert (
        esquema and esquema != "public" and re.fullmatch(r"[a-z_][a-z0-9_]*", esquema)
    )
    url = postgres_engine.url
    secreto = secrets.token_hex(32)
    log = tmp_path / "uvicorn.log"

    with TemporaryDirectory(prefix="mail-", dir=tmp_path) as correo:
        entorno = {
            **os.environ,
            "DB_HOST": url.host,
            "DB_PORT": str(url.port or 5432),
            "DB_NAME": url.database,
            "DB_USER": url.username,
            "DB_PASSWORD": url.password,
            # Use the same validated loopback destination as the PostgreSQL fixture.
            "PGHOSTADDR": "127.0.0.1" if url.host == "localhost" else url.host,
            "PGOPTIONS": f"-c search_path={esquema}",
            "JWT_SECRET_KEY": secreto,
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "REFRESH_TOKEN_EXPIRE_DAYS": "7",
            "RECOVERY_TOKEN_EXPIRE_MINUTES": "10",
            "RECOVERY_MAIL_DIR": correo,
            "PYTHONIOENCODING": "utf-8",
        }
        with log.open("wb") as salida:
            proceso = subprocess.Popen(
                [sys.executable, "-m", "tests.support.serve_e2e"],
                cwd=ROOT,
                env=entorno,
                stdin=subprocess.PIPE,
                stdout=salida,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                base_url = _esperar_url(proceso, log)
                with httpx2.Client(
                    base_url=base_url, trust_env=False, timeout=10
                ) as http:
                    respuesta = http.get("/")
                    assert respuesta.status_code == 200
                    assert respuesta.json()["status"] == "ok"
                    yield ServidorE2E(http, Path(correo), secreto)
            finally:
                if proceso.stdin is not None:
                    proceso.stdin.close()
                try:
                    proceso.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proceso.kill()
                    proceso.wait(timeout=5)


@pytest.fixture
def preparar_personal(postgres_engine):
    """Provision staff in the disposable DB, keeping public registration at cliente."""

    def preparar(rol: str) -> dict[str, str]:
        credenciales = {
            "email": f"{rol}-{uuid4().hex}@example.com",
            "password": secrets.token_urlsafe(24),
        }
        with Session(postgres_engine) as db:
            db.add(
                UsuarioORM(
                    nombre=f"Personal de prueba {rol}",
                    email=credenciales["email"],
                    password_hash=hash_password(credenciales["password"]),
                    rol=rol,
                )
            )
            db.commit()
        return credenciales

    return preparar
