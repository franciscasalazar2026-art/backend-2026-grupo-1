from datetime import datetime
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

    def cliente_activo(self, cliente_id: int) -> bool:
        ...

    def servicio_activo(self, servicio_id: int):
        ...

    def profesional_activo(self, profesional_id: int) -> bool:
        ...

    def profesional_tiene_servicio(
        self,
        profesional_id: int,
        servicio_id: int,
    ) -> bool:
        ...

    def tiene_conflicto_horario(
        self,
        profesional_id: int,
        inicio: datetime,
        fin: datetime,
        excluir_cita_id: int | None = None,
    ) -> bool:
        ...

    def crear(self, datos: dict):
        ...

    def actualizar(self, cita, cambios: dict):
        ...

    def eliminar(self, cita):
        ...
