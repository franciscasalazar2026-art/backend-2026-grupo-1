
from math import ceil

from app.application.puertos.profesional_repositorio import (
    ProfesionalRepositorio,
    ConflictoRepositorio,
)


class ProfesionalNoEncontrado(Exception):
    pass


class ProfesionalInactivo(Exception):
    pass


class ServicioNoEncontrado(Exception):
    pass


class ServicioProfesional:

    def __init__(self, repositorio: ProfesionalRepositorio):
        self.repositorio = repositorio

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        pagina=1,
        limite=10,
    ):
        profesionales, total = self.repositorio.listar(
            buscar=buscar,
            solo_activos=solo_activos,
            pagina=pagina,
            limite=limite,
        )

        return {
            "items": profesionales,
            "total": total,
            "pagina": pagina,
            "limite": limite,
            "total_paginas": ceil(total / limite) if total else 1,
        }

    def crear(self, datos: dict):
        try:
            return self.repositorio.crear(datos)
        except ConflictoRepositorio:
            raise ValueError(
                "El correo del profesional ya está registrado."
            )

    def obtener(self, profesional_id: int):
        profesional = self.repositorio.obtener(profesional_id)

        if profesional is None:
            raise ProfesionalNoEncontrado()

        return profesional

    def actualizar(self, profesional_id: int, cambios: dict):
        profesional = self.obtener(profesional_id)

        if any(valor is None for valor in cambios.values()):
            raise ValueError("Los campos no pueden ser nulos.")

        try:
            return self.repositorio.actualizar(
                profesional,
                cambios,
            )
        except ConflictoRepositorio:
            raise ValueError(
                "No se pudo actualizar el profesional."
            )

    def desactivar(self, profesional_id: int):
        profesional = self.obtener(profesional_id)
        self.repositorio.desactivar(profesional)

    def restaurar(self, profesional_id: int):
        profesional = self.obtener(profesional_id)
        return self.repositorio.restaurar(profesional)

    def listar_servicios(self, profesional_id: int):
        profesional = self.obtener(profesional_id)
        return self.repositorio.listar_servicios(profesional)

    def asignar_servicio(
        self,
        profesional_id: int,
        servicio_id: int,
    ):
        profesional = self.obtener(profesional_id)

        if not profesional.activo:
            raise ProfesionalInactivo()

        if (
            not isinstance(servicio_id, int)
            or isinstance(servicio_id, bool)
            or servicio_id <= 0
        ):
            raise ValueError(
                "servicio_id debe ser un entero positivo."
            )

        servicio = self.repositorio.obtener_servicio(servicio_id)

        if servicio is None or not servicio.activo:
            raise ServicioNoEncontrado()

        try:
            resultado = self.repositorio.asignar_servicio(
                profesional_id,
                servicio_id,
            )

            if resultado is None:
                raise ValueError("El servicio ya está asignado.")

            return resultado

        except ConflictoRepositorio:
            raise ValueError("No se pudo asignar el servicio.")
