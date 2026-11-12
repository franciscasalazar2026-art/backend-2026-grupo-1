
from typing import Protocol


class ConflictoRepositorio(Exception):
    """Error cuando existe un conflicto al guardar información."""


class ProfesionalRepositorio(Protocol):

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        pagina=1,
        limite=10,
    ):
        ...

    def obtener(self, profesional_id: int):
        ...

    def obtener_servicio(self, servicio_id: int):
        ...

    def crear(self, datos: dict):
        ...

    def actualizar(self, profesional, cambios: dict):
        ...

    def desactivar(self, profesional):
        ...

    def restaurar(self, profesional):
        ...

    def listar_servicios(self, profesional):
        ...

    def asignar_servicio(
        self,
        profesional_id: int,
        servicio_id: int,
    ):
        ...
