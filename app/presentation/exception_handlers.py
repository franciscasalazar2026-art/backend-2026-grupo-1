from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# El valor numérico conserva compatibilidad con versiones anteriores de Starlette.
HTTP_422_UNPROCESSABLE_CONTENT = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


def _extraer_mensaje_uniforme(raw_detail) -> str:
    if isinstance(raw_detail, str):
        return raw_detail
    if isinstance(raw_detail, dict):
        return str(
            raw_detail.get("mensaje")
            or raw_detail.get("message")
            or raw_detail.get("detail")
            or raw_detail
        )
    if isinstance(raw_detail, list):
        mensajes = []
        for err in raw_detail:
            if isinstance(err, dict):
                campo = " -> ".join(
                    str(loc) for loc in err.get("loc", []) if loc != "body"
                )
                msg = err.get("msg", "Dato inválido")
                mensajes.append(f"{campo}: {msg}" if campo else msg)
            else:
                mensajes.append(str(err))
        return "; ".join(mensajes) if mensajes else "Error de validación en los datos enviados."
    return str(raw_detail)


def registrar_manejadores_errores(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        mensaje = _extraer_mensaje_uniforme(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "mensaje": mensaje,
                "detail": mensaje,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        mensaje = _extraer_mensaje_uniforme(exc.errors())
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "VALIDATION_ERROR",
                "mensaje": mensaje,
                "detail": mensaje,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "mensaje": "Ocurrió un error interno inesperado en el servidor.",
                "detail": "Ocurrió un error interno inesperado en el servidor.",
            },
        )
