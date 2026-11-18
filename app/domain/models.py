from enum import Enum
from typing import Protocol


class EstadoCita(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"


class UsuarioAutenticado(Protocol):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
