
from typing import Protocol

from app.domain.models import EstadoCita


class CitaRepositorio(Protocol):

    def listar(
        self,
        estado: EstadoCita | None = None,
        ordenar_por="fecha_hora",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        ...

    def obtener(self, cita_id: int):
        ...

    def crear(self, datos: dict):
        ...

    def actualizar(self, cita, cambios: dict):
        ...

    def eliminar(self, cita):
        ...
