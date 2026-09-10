from datetime import datetime
from app.models import EstadoCita
from app.schemas import Cliente, Cita

# Base de datos en memoria para clientes
db_clientes = [
    Cliente(id=1, nombre="Juan Pérez", email="juan.perez@example.com", telefono="912345678"),
    Cliente(id=2, nombre="María López", email="maria.lopez@example.com", telefono="987654321")
]

# Base de datos en memoria para citas
db_citas = [
    Cita(
        id=1, 
        cliente_id=1, 
        fecha_hora=datetime(2026, 9, 15, 10, 0), 
        motivo="Consulta general", 
        estado=EstadoCita.PENDIENTE
    )
]