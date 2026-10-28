from fastapi import FastAPI

from app.routers import clientes, citas, servicios


app = FastAPI(
    title="API REST - Sistema de Gestión de Citas",
    description="API Backend para la gestión de clientes, citas y servicios.",
    version="1.0.0",
)

app.include_router(clientes.router)
app.include_router(citas.router)
app.include_router(servicios.router)
