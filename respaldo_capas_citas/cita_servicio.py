
from math import ceil

from app.application.puertos.cita_repositorio import CitaRepositorio


class CitaNoEncontrada(Exception):
    pass


class CitaServicio:

    def __init__(self, repositorio: CitaRepositorio):
        self.repositorio = repositorio

    def listar(
        self,
        estado=None,
        ordenar_por="fecha_hora",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        citas, total = self.repositorio.listar(
            estado=estado,
            ordenar_por=ordenar_por,
            direccion=direccion,
            pagina=pagina,
            limite=limite,
        )

        return {
            "items": citas,
            "total": total,
            "pagina": pagina,
            "limite": limite,
            "total_paginas": ceil(total / limite) if total else 1,
        }

    def obtener(self, cita_id: int):
        cita = self.repositorio.obtener(cita_id)

        if cita is None:
            raise CitaNoEncontrada()

        return cita

    def crear(self, datos: dict):
        return self.repositorio.crear(datos)

    def actualizar(self, cita_id: int, cambios: dict):
        cita = self.obtener(cita_id)
        return self.repositorio.actualizar(cita, cambios)

    def eliminar(self, cita_id: int):
        cita = self.obtener(cita_id)
        self.repositorio.eliminar(cita)
