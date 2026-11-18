from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.infrastructure.models.refresh_token import RefreshTokenORM
from app.infrastructure.models.token_recuperacion import TokenRecuperacionUsadoORM
from app.infrastructure.models.usuario import UsuarioORM


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, usuario_id: int) -> UsuarioORM | None:
        return self.db.query(UsuarioORM).filter(UsuarioORM.id == usuario_id).first()

    def obtener_por_email(self, email: str) -> UsuarioORM | None:
        return (
            self.db.query(UsuarioORM)
            .filter(UsuarioORM.email == email.strip().lower())
            .first()
        )

    def crear_usuario(
        self,
        nombre: str,
        email: str,
        password_hash: str,
        rol: str = "cliente",
    ) -> UsuarioORM:
        usuario = UsuarioORM(
            nombre=nombre.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            rol=rol,
            activo=True,
            token_version=1,
            intentos_fallidos=0,
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def actualizar_usuario(self, usuario: UsuarioORM) -> UsuarioORM:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    # --- Gestión de Refresh Tokens ---
    def guardar_refresh_token(
        self,
        usuario_id: int,
        token_hash: str,
        familia_id: str,
        expira_en: datetime,
    ) -> RefreshTokenORM:
        registro = RefreshTokenORM(
            usuario_id=usuario_id,
            token_hash=token_hash,
            familia_id=familia_id,
            revocado=False,
            expira_en=expira_en,
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def obtener_refresh_token(self, token_hash: str) -> RefreshTokenORM | None:
        return (
            self.db.query(RefreshTokenORM)
            .filter(RefreshTokenORM.token_hash == token_hash)
            .first()
        )

    def revocar_refresh_token(self, registro: RefreshTokenORM) -> None:
        registro.revocado = True
        self.db.commit()

    def revocar_familia_tokens(self, familia_id: str) -> None:
        self.db.execute(
            update(RefreshTokenORM)
            .where(RefreshTokenORM.familia_id == familia_id)
            .values(revocado=True)
        )
        self.db.commit()

    def jti_ya_consumido(self, jti: str) -> bool:
        existe = (
            self.db.query(TokenRecuperacionUsadoORM)
            .filter(TokenRecuperacionUsadoORM.jti == jti)
            .first()
        )
        return existe is not None

    def consumir_recuperacion(
        self,
        usuario_id: int,
        version: int,
        jti: str,
        password_hash: str,
    ) -> Literal["actualizado", "consumido", "usuario_invalido", "desactualizado"]:
        with self.db.begin():
            # Serializa restablecimientos del mismo usuario incluso con distintos JWT.
            usuario = self.db.scalar(
                select(UsuarioORM).where(UsuarioORM.id == usuario_id).with_for_update()
            )
            if usuario is None or not usuario.activo:
                return "usuario_invalido"
            if self.jti_ya_consumido(jti):
                return "consumido"
            if usuario.token_version != version:
                return "desactualizado"

            usuario.password_hash = password_hash
            usuario.token_version += 1
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            self.db.add(
                TokenRecuperacionUsadoORM(
                    jti=jti,
                    usuario_id=usuario_id,
                    consumido_en=datetime.now(timezone.utc),
                )
            )
            self.db.execute(
                update(RefreshTokenORM)
                .where(RefreshTokenORM.usuario_id == usuario_id)
                .values(revocado=True)
            )
        return "actualizado"
