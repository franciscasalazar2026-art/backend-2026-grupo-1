
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Servicio:
    nombre: str
    duracion_minutos: int
    precio: Decimal
    descripcion: str | None = None
    activo: bool = True
    id: int | None = None
