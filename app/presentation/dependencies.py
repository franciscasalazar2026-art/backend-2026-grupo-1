from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models.usuario import UsuarioORM
from app.infrastructure.security import decode_and_validate_token

from app.infrastructure.repositories.profesional_repository import (
    ProfesionalRepository,
)
from app.infrastructure.repositories.cliente_repository import (
    ClienteRepository,
)

from app.application.services.profesional_servicio import (
    ServicioProfesional,
)
from app.application.services.cliente_servicio import (
    ClienteServicio,
)

from app.infrastructure.repositories.servicio_repository import (
    ServicioRepository,
)

from app.application.services.servicio_servicio import (
    ServicioAplicacion,
)

from app.infrastructure.repositories.cita_repository import (
    CitaRepository,
)

from app.application.services.cita_servicio import (
    CitaServicio,
)

from app.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)

from app.application.services.auth_servicio import (
    AuthServicio,
)

bearer_scheme = HTTPBearer(auto_error=False)


def obtener_servicio_profesional(
    db: Session = Depends(get_db),
) -> ServicioProfesional:
    repositorio = ProfesionalRepository(db)
    return ServicioProfesional(repositorio)


def obtener_servicio_cliente(
    db: Session = Depends(get_db),
) -> ClienteServicio:
    repositorio = ClienteRepository(db)
    return ClienteServicio(repositorio)


def obtener_servicio_aplicacion(
    db: Session = Depends(get_db),
) -> ServicioAplicacion:
    repositorio = ServicioRepository(db)
    return ServicioAplicacion(repositorio)


def obtener_servicio_cita(
    db: Session = Depends(get_db),
) -> CitaServicio:
    repositorio = CitaRepository(db)
    return CitaServicio(repositorio)


def obtener_servicio_auth(
    db: Session = Depends(get_db),
) -> AuthServicio:
    repositorio = UsuarioRepository(db)
    return AuthServicio(repositorio)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    """Valida el Access JWT Bearer y retorna el usuario autenticado (401 si falla)."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación no proporcionadas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_and_validate_token(
            credentials.credentials, expected_type="access"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    sub = payload.get("sub")
    token_ver = payload.get("ver")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UsuarioRepository(db)
    usuario = repo.obtener_por_id(int(sub))
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica que la sesión no haya sido invalidada por un restablecimiento de contraseña
    if token_ver is not None and usuario.token_version != token_ver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión fue invalidada. Inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def require_role(*roles_permitidos: str):
    """Verifica que el usuario autenticado posea alguno de los roles permitidos (403 si no)."""
    def _verificar_rol(
        usuario_actual: UsuarioORM = Depends(get_current_user),
    ) -> UsuarioORM:
        if usuario_actual.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta operación.",
            )
        return usuario_actual

    return _verificar_rol
