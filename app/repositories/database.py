from app.domain.models import EstadoCita
from app.schemas.schemas import Cliente, Cita

db_clientes = [
    Cliente(id=1, nombre="Juan Pérez", email="juan.perez@example.com", telefono="912345678", activo=True),
    Cliente(id=2, nombre="María López", email="maria.lopez@example.com", telefono="987654321", activo=True)
]

db_citas = [
    Cita(
        id=1,
        cliente_id=1,
        servicio_id=1,
        profesional_id=1,
        fecha_hora="2026-09-15T10:00:00",
        motivo="Consulta general",
        estado=EstadoCita.PENDIENTE
    )
]