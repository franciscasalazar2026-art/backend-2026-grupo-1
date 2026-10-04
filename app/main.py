from fastapi import FastAPI
from app.routers import clientes, citas

app = FastAPI(
    title="API REST - Sistema de Gestión de Citas",
    description="API Backend para la gestión de clientes y citas.",
    version="1.0.0"
)

# Conecta las rutas de cada módulo
app.include_router(clientes.router)
app.include_router(citas.router)