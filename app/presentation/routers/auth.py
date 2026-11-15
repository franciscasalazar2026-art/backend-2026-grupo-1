from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.auth_servicio import AuthError, AuthServicio
from app.infrastructure.models.usuario import UsuarioORM
from app.presentation.dependencies import get_current_user, obtener_servicio_auth
from app.presentation.schemas.dtos.auth_dto import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MensajeResponse,
    RefreshRequest,
    RegistroUsuarioRequest,
    ResetPasswordRequest,
    TokenResponse,
    UsuarioResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticación y Seguridad"])


@router.post(
    "/registro",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def registrar_usuario(
    datos: RegistroUsuarioRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    try:
        return servicio.registrar_usuario(
            nombre=datos.nombre,
            email=datos.email,
            password=datos.password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión y obtener Access + Refresh tokens",
)
def iniciar_sesion(
    datos: LoginRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    try:
        return servicio.iniciar_sesion(email=datos.email, password=datos.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Obtener perfil del usuario autenticado",
)
def obtener_usuario_actual(
    usuario_actual: UsuarioORM = Depends(get_current_user),
):
    return usuario_actual


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar Access JWT rotando el Refresh Token",
)
def renovar_tokens(
    datos: RefreshRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    try:
        return servicio.renovar_tokens(raw_refresh_token=datos.refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/logout",
    response_model=MensajeResponse,
    summary="Cerrar sesión revocando el Refresh Token",
)
def cerrar_sesion(
    datos: LogoutRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    servicio.cerrar_sesion(raw_refresh_token=datos.refresh_token)
    return MensajeResponse(mensaje="Sesión cerrada correctamente.")


@router.post(
    "/forgot-password",
    response_model=MensajeResponse,
    summary="Solicitar enlace/token de recuperación de contraseña",
)
def solicitar_recuperacion(
    datos: ForgotPasswordRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    resultado = servicio.solicitar_recuperacion(email=datos.email)
    return MensajeResponse(**resultado)


@router.post(
    "/reset-password",
    response_model=MensajeResponse,
    summary="Restablecer contraseña con JWT de propósito exclusivo y uso único",
)
def restablecer_contrasena(
    datos: ResetPasswordRequest,
    servicio: AuthServicio = Depends(obtener_servicio_auth),
):
    try:
        servicio.restablecer_contrasena(
            recovery_token=datos.token,
            nueva_password=datos.nueva_password,
        )
        return MensajeResponse(
            mensaje="Contraseña restablecida con éxito. Inicia sesión nuevamente."
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
