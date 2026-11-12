
from typing import Protocol

from app.application.puertos.profesional_repositorio import (
    ConflictoRepositorio,
)


class ClienteRepositorio(Protocol):

    def listar(self, limite=10, desplazamiento=0):
        ...

    def obtener(self, cliente_id: int):
        ...

    def crear(self, datos: dict):
        ...

    def actualizar(self, cliente, cambios: dict):
        ...

    def eliminar(self, cliente):
        ...
