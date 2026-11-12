
from dataclasses import dataclass


@dataclass
class Cliente:
    nombre: str
    email: str
    telefono: str
    activo: bool = True
    id: int | None = None
