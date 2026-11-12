
from dataclasses import dataclass


@dataclass
class Profesional:
    nombre: str
    especialidad: str
    email: str
    telefono: str
    activo: bool = True
    id: int | None = None
