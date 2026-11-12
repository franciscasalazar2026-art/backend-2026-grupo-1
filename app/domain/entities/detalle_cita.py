
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class DetalleCita:
    servicio_id: int
    servicio_nombre: str
    profesional_id: int
    profesional_nombre: str
    fecha_hora_inicio: datetime
    duracion_minutos: int
    precio: Decimal
    id: int | None = None
