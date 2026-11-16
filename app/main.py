from fastapi import FastAPI

from app.presentation.exception_handlers import registrar_manejadores_errores
from app.presentation.routers import (
    auth,
    citas,
    clientes,
    profesionales,
    servicios,
)

app = FastAPI(
    title="API REST - Sistema de Gestión de Citas",
    description=(
        "API Backend para la gestión de clientes, citas, servicios y profesionales "
        "con autenticación JWT, control de roles y recuperación de contraseña."
    ),
    version="1.0.0",
)

registrar_manejadores_errores(app)


@app.get("/", tags=["Salud"], summary="Verificar estado de la API")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(citas.router)
app.include_router(servicios.router)
app.include_router(profesionales.router)
