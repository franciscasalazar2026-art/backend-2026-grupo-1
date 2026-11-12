
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.models import EstadoCita
from app.domain.entities.detalle_cita import DetalleCita


@dataclass
class Cita:
    cliente_id: int
    fecha_hora: datetime
    motivo: str
    estado: EstadoCita
    servicios: list[DetalleCita] = field(default_factory=list)
    id: int | None = None
