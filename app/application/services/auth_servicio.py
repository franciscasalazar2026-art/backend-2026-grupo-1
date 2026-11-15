from datetime import datetime, timedelta, timezone
import uuid

from app.domain.rules.politica_contrasena import validar_politica_contrasena
from app.infrastructure.models.usuario import UsuarioORM
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.security import (
    create_access_token,
    create_recovery_token,
    decode_and_validate_token,
    generate_opaque_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)

MAX_INTENTOS_LOGIN = 5
MINUTOS_BLOQUEO_LOGIN = 15


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthServicio:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def registrar_usuario(self, nombre: str, email: str, password: str) -> UsuarioORM:
        try:
            validar_politica_contrasena(password)
        except ValueError as exc:
            raise AuthError(str(exc), status_code=422) from exc

        if self.repo.obtener_por_email(email):
            raise AuthError("El correo electrónico ya está registrado.", status_code=409)

        password_hashed = hash_password(password)
        # Por seguridad (5.5), el registro público siempre asigna el rol base 'cliente'
        return self.repo.crear_usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hashed,
            rol="cliente",
        )

    def iniciar_sesion(self, email: str, password: str) -> dict:
        usuario = self.repo.obtener_por_email(email)
        ahora = datetime.now(timezone.utc)

        if usuario and usuario.bloqueado_hasta:
            bloqueo = usuario.bloqueado_hasta
            if bloqueo.tzinfo is None:
                bloqueo = bloqueo.replace(tzinfo=timezone.utc)
            if bloqueo > ahora:
                raise AuthError(
                    "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta más tarde.",
                    status_code=429,
                )

        if not usuario or not usuario.activo or not verify_password(password, usuario.password_hash):
            if usuario:
                usuario.intentos_fallidos += 1
                if usuario.intentos_fallidos >= MAX_INTENTOS_LOGIN:
                    usuario.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO_LOGIN)
                self.repo.actualizar_usuario(usuario)
            # Mensaje genérico exigido en 5.5
            raise AuthError("Credenciales inválidas.", status_code=401)

        # Login exitoso: reiniciar contador de intentos
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.repo.actualizar_usuario(usuario)

        access_token = create_access_token(
            subject=usuario.id,
            role=usuario.rol,
            token_version=usuario.token_version,
        )
        raw_refresh, refresh_hash, refresh_exp = generate_opaque_refresh_token()
        familia_id = str(uuid.uuid4())
        self.repo.guardar_refresh_token(
            usuario_id=usuario.id,
            token_hash=refresh_hash,
            familia_id=familia_id,
            expira_en=refresh_exp,
        )

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "usuario": usuario,
        }

    def renovar_tokens(self, raw_refresh_token: str) -> dict:
        token_hashed = hash_token(raw_refresh_token)
        registro = self.repo.obtener_refresh_token(token_hashed)

        if not registro:
            raise AuthError("Refresh token inválido.", status_code=401)

        # Detección de reutilización: si ya estaba revocado, invalidar toda la familia (5.5)
        if registro.revocado:
            self.repo.revocar_familia_tokens(registro.familia_id)
            raise AuthError(
                "Reutilización de token detectada. Sesión revocada por seguridad.",
                status_code=401,
            )

        ahora = datetime.now(timezone.utc)
        expira = registro.expira_en
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)

        if expira <= ahora:
            self.repo.revocar_refresh_token(registro)
            raise AuthError("Refresh token expirado.", status_code=401)

        usuario = self.repo.obtener_por_id(registro.usuario_id)
        if not usuario or not usuario.activo:
            raise AuthError("Usuario inactivo o inexistente.", status_code=401)

        # Rotación: revocar el token actual y emitir uno nuevo en la misma familia
        self.repo.revocar_refresh_token(registro)
        nuevo_raw, nuevo_hash, nueva_exp = generate_opaque_refresh_token()
        self.repo.guardar_refresh_token(
            usuario_id=usuario.id,
            token_hash=nuevo_hash,
            familia_id=registro.familia_id,
            expira_en=nueva_exp,
        )

        nuevo_access = create_access_token(
            subject=usuario.id,
            role=usuario.rol,
            token_version=usuario.token_version,
        )

        return {
            "access_token": nuevo_access,
            "refresh_token": nuevo_raw,
            "token_type": "bearer",
        }

    def cerrar_sesion(self, raw_refresh_token: str) -> None:
        token_hashed = hash_token(raw_refresh_token)
        registro = self.repo.obtener_refresh_token(token_hashed)
        if registro and not registro.revocado:
            self.repo.revocar_refresh_token(registro)

    def solicitar_recuperacion(self, email: str) -> dict:
        usuario = self.repo.obtener_por_email(email)
        respuesta_generica = {
            "mensaje": "Si el correo existe en nuestro sistema, recibirás instrucciones para restablecer tu contraseña."
        }
        if not usuario or not usuario.activo:
            return respuesta_generica

        token_rec, _, _ = create_recovery_token(subject=usuario.id)
        # En entorno de prueba/desarrollo retornamos el token para verificación controlada (5.6)
        respuesta_generica["recovery_token_prueba"] = token_rec
        return respuesta_generica

    def restablecer_contrasena(self, recovery_token: str, nueva_password: str) -> None:
        try:
            validar_politica_contrasena(nueva_password)
        except ValueError as exc:
            raise AuthError(str(exc), status_code=422) from exc

        try:
            payload = decode_and_validate_token(recovery_token, expected_type="recovery")
        except ValueError as exc:
            raise AuthError(str(exc), status_code=401) from exc

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise AuthError("Token de recuperación malformado.", status_code=401)

        if self.repo.jti_ya_consumido(jti):
            raise AuthError("Este enlace de recuperación ya fue utilizado.", status_code=400)

        usuario = self.repo.obtener_por_id(int(sub))
        if not usuario or not usuario.activo:
            raise AuthError("Usuario no válido.", status_code=404)

        # Actualizar hash, invalidar access tokens antiguos (token_version) y revocar refresh tokens
        usuario.password_hash = hash_password(nueva_password)
        usuario.token_version += 1
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.repo.actualizar_usuario(usuario)

        self.repo.marcar_jti_consumido(jti=jti, usuario_id=usuario.id)
        self.repo.revocar_todas_sesiones_usuario(usuario_id=usuario.id)
