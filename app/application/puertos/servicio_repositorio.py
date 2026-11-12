
from typing import Protocol


class ServicioRepositorio(Protocol):

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        ordenar_por="precio",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        ...

    def obtener(self, servicio_id: int):
        ...

    def crear(self, datos: dict):
        ...

    def actualizar(self, servicio, cambios: dict):
        ...

    def desactivar(self, servicio):
        ...

    def restaurar(self, servicio):
        ...
