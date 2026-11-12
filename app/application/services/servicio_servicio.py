
from math import ceil

from app.application.puertos.servicio_repositorio import (
    ServicioRepositorio,
)


class ServicioNoEncontrado(Exception):
    pass


class ServicioAplicacion:

    def __init__(self, repositorio: ServicioRepositorio):
        self.repositorio = repositorio

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        ordenar_por="precio",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        servicios, total = self.repositorio.listar(
            buscar=buscar,
            solo_activos=solo_activos,
            ordenar_por=ordenar_por,
            direccion=direccion,
            pagina=pagina,
            limite=limite,
        )

        return {
            "items": servicios,
            "total": total,
            "pagina": pagina,
            "limite": limite,
            "total_paginas": ceil(total / limite) if total else 1,
        }

    def obtener(self, servicio_id: int):
        servicio = self.repositorio.obtener(servicio_id)

        if servicio is None:
            raise ServicioNoEncontrado()

        return servicio

    def crear(self, datos: dict):
        return self.repositorio.crear(datos)

    def actualizar(self, servicio_id: int, cambios: dict):
        servicio = self.obtener(servicio_id)

        if any(valor is None for valor in cambios.values()):
            raise ValueError("Los campos no pueden ser nulos.")

        return self.repositorio.actualizar(servicio, cambios)

    def desactivar(self, servicio_id: int):
        servicio = self.obtener(servicio_id)
        self.repositorio.desactivar(servicio)

    def restaurar(self, servicio_id: int):
        servicio = self.obtener(servicio_id)
        return self.repositorio.restaurar(servicio)
