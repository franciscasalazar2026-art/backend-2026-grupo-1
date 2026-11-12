
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session, joinedload

from app.domain.models import EstadoCita
from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    DetalleReservaORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)
from app.infrastructure.mappers.cita_mapper import CitaMapper
from app.application.puertos.cita_repositorio import CitaRepositorio


class CitaRepository(CitaRepositorio):

    def __init__(self, db: Session):
        self.db = db

    def _opciones_cita(self):
        ruta = (
            joinedload(CitaORM.reserva)
            .joinedload(ReservaORM.detalles)
            .joinedload(DetalleReservaORM.profesional_servicio)
        )

        return (
            ruta.joinedload(ProfesionalServicioORM.profesional),
            ruta.joinedload(ProfesionalServicioORM.servicio),
        )

    def _buscar_modelo(self, cita_id: int):
        consulta = (
            select(CitaORM)
            .options(*self._opciones_cita())
            .where(CitaORM.id == cita_id)
        )

        return self.db.scalars(consulta).unique().first()

    def _convertir(self, cita: CitaORM):
        reserva = cita.reserva
        detalles = sorted(reserva.detalles, key=lambda d: d.id)

        servicios = []

        for detalle in detalles:
            relacion = detalle.profesional_servicio

            servicios.append({
                "servicio_id": relacion.servicio.id,
                "servicio_nombre": relacion.servicio.nombre,
                "profesional_id": relacion.profesional.id,
                "profesional_nombre": relacion.profesional.nombre,
                "fecha_hora_inicio": detalle.fecha_hora_inicio,
                "duracion_minutos": detalle.duracion_minutos,
                "precio": detalle.precio,
            })

        return CitaMapper.a_entidad({
            "id": cita.id,
            "cliente_id": reserva.cliente_id,
            "fecha_hora": cita.fecha_hora,
            "motivo": cita.motivo,
            "estado": cita.estado,
            "servicios": servicios,
        })

    def _validar_fecha_futura(self, fecha):
        ahora = (
            datetime.now(fecha.tzinfo)
            if fecha.tzinfo is not None
            else datetime.now()
        )

        if fecha <= ahora:
            raise ValueError(
                "No se puede agendar una cita en el pasado."
            )

    def _esta_cancelada(self, estado):
        valor = str(getattr(estado, "value", estado)).lower()
        return "cancel" in valor or "anulad" in valor

    def _tiene_conflicto(
        self,
        profesional_id,
        inicio,
        fin,
        excluir_cita_id: Optional[int] = None,
    ):
        consulta = (
            select(DetalleReservaORM, CitaORM)
            .join(
                ReservaORM,
                DetalleReservaORM.reserva_id == ReservaORM.id,
            )
            .join(
                CitaORM,
                CitaORM.reserva_id == ReservaORM.id,
            )
            .join(
                ProfesionalServicioORM,
                DetalleReservaORM.profesional_servicio_id
                == ProfesionalServicioORM.id,
            )
            .where(
                ProfesionalServicioORM.profesional_id == profesional_id
            )
        )

        for detalle, cita in self.db.execute(consulta):

            if (
                excluir_cita_id is not None
                and cita.id == excluir_cita_id
            ):
                continue

            if self._esta_cancelada(cita.estado):
                continue

            inicio_existente = detalle.fecha_hora_inicio
            fin_existente = inicio_existente + timedelta(
                minutes=detalle.duracion_minutos
            )

            inicio_nuevo = inicio
            fin_nuevo = fin

            if (
                inicio_existente.tzinfo is None
                and inicio_nuevo.tzinfo is not None
            ):
                inicio_existente = inicio_existente.replace(
                    tzinfo=inicio_nuevo.tzinfo
                )
                fin_existente = fin_existente.replace(
                    tzinfo=inicio_nuevo.tzinfo
                )

            elif (
                inicio_existente.tzinfo is not None
                and inicio_nuevo.tzinfo is None
            ):
                inicio_nuevo = inicio_nuevo.replace(
                    tzinfo=inicio_existente.tzinfo
                )
                fin_nuevo = fin_nuevo.replace(
                    tzinfo=inicio_existente.tzinfo
                )

            if (
                inicio_nuevo < fin_existente
                and inicio_existente < fin_nuevo
            ):
                return True

        return False

    def listar(
        self,
        estado=None,
        ordenar_por="fecha_hora",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        filtros = []

        if estado is not None:
            filtros.append(CitaORM.estado == estado)

        total = self.db.scalar(
            select(func.count(CitaORM.id)).where(*filtros)
        ) or 0

        campos = {
            "id": CitaORM.id,
            "fecha_hora": CitaORM.fecha_hora,
            "estado": CitaORM.estado,
        }

        campo = campos.get(
            ordenar_por,
            CitaORM.fecha_hora,
        )

        campo = (
            campo.desc()
            if direccion == "desc"
            else campo.asc()
        )

        consulta = (
            select(CitaORM)
            .options(*self._opciones_cita())
            .where(*filtros)
            .order_by(campo)
            .offset((pagina - 1) * limite)
            .limit(limite)
        )

        modelos = self.db.scalars(consulta).unique().all()

        return [
            self._convertir(cita)
            for cita in modelos
        ], total

    def obtener(self, cita_id: int):
        modelo = self._buscar_modelo(cita_id)

        if modelo is None:
            return None

        return self._convertir(modelo)

    def crear(self, datos: dict):
        cliente = self.db.get(
            ClienteORM,
            datos["cliente_id"],
        )

        if cliente is None or not cliente.activo:
            raise ValueError(
                "El cliente no existe o está inactivo."
            )

        fecha = datetime.combine(
            datos["fecha"],
            datos["hora"],
        )

        self._validar_fecha_futura(fecha)

        servicios_validados = []
        hora_actual = fecha

        for item in datos["servicios"]:

            servicio = self.db.get(
                ServicioORM,
                item["servicio_id"],
            )

            profesional = self.db.get(
                ProfesionalORM,
                item["profesional_id"],
            )

            if servicio is None or not servicio.activo:
                raise ValueError(
                    "El servicio no existe o está inactivo."
                )

            if profesional is None or not profesional.activo:
                raise ValueError(
                    "El profesional no existe o está inactivo."
                )

            relacion = self.db.scalar(
                select(ProfesionalServicioORM).where(
                    ProfesionalServicioORM.profesional_id
                    == profesional.id,
                    ProfesionalServicioORM.servicio_id
                    == servicio.id,
                )
            )

            if relacion is None:
                raise ValueError(
                    "El profesional no tiene asociado el servicio."
                )

            fin_servicio = hora_actual + timedelta(
                minutes=servicio.duracion_minutos
            )

            if self._tiene_conflicto(
                profesional.id,
                hora_actual,
                fin_servicio,
            ):
                raise RuntimeError(
                    "El profesional ya tiene una atención en ese horario."
                )

            servicios_validados.append(
                (relacion, servicio, hora_actual)
            )

            hora_actual = fin_servicio

        try:
            reserva = ReservaORM(
                cliente_id=cliente.id
            )

            self.db.add(reserva)
            self.db.flush()

            for relacion, servicio, hora_inicio in servicios_validados:

                self.db.add(
                    DetalleReservaORM(
                        reserva_id=reserva.id,
                        profesional_servicio_id=relacion.id,
                        fecha_hora_inicio=hora_inicio,
                        duracion_minutos=servicio.duracion_minutos,
                        precio=servicio.precio,
                    )
                )

            nueva_cita = CitaORM(
                reserva_id=reserva.id,
                fecha_hora=fecha,
                motivo=datos["motivo"],
                estado=EstadoCita.PENDIENTE,
            )

            self.db.add(nueva_cita)
            self.db.flush()

            nuevo_id = nueva_cita.id

            self.db.commit()

            guardada = self._buscar_modelo(nuevo_id)

            return self._convertir(guardada)

        except IntegrityError as error:
            self.db.rollback()

            raise RuntimeError(
                "Conflicto al registrar la cita."
            ) from error

    def actualizar(self, cita, cambios: dict):
        modelo = self._buscar_modelo(cita.id)

        if modelo is None:
            return None

        # ACTUALIZAR FECHA Y HORA
        if "fecha" in cambios or "hora" in cambios:

            if "fecha" in cambios and cambios["fecha"] is None:
                raise ValueError(
                    "La fecha no puede ser nula."
                )

            if "hora" in cambios and cambios["hora"] is None:
                raise ValueError(
                    "La hora no puede ser nula."
                )

            fecha_actual = modelo.fecha_hora.date()
            hora_actual = modelo.fecha_hora.time()

            nueva_fecha = cambios.get(
                "fecha",
                fecha_actual,
            )

            nueva_hora = cambios.get(
                "hora",
                hora_actual,
            )

            fecha_completa = datetime.combine(
                nueva_fecha,
                nueva_hora,
            )

            self._validar_fecha_futura(fecha_completa)

            hora_inicio = fecha_completa
            horarios = []

            for detalle in sorted(
                modelo.reserva.detalles,
                key=lambda d: d.id,
            ):

                fin = hora_inicio + timedelta(
                    minutes=detalle.duracion_minutos
                )

                profesional_id = (
                    detalle.profesional_servicio.profesional_id
                )

                if self._tiene_conflicto(
                    profesional_id,
                    hora_inicio,
                    fin,
                    excluir_cita_id=modelo.id,
                ):
                    raise RuntimeError(
                        "El nuevo horario entra en conflicto "
                        "con otra atención."
                    )

                horarios.append(
                    (detalle, hora_inicio)
                )

                hora_inicio = fin

            modelo.fecha_hora = fecha_completa

            for detalle, inicio in horarios:
                detalle.fecha_hora_inicio = inicio

        # ACTUALIZAR MOTIVO
        if "motivo" in cambios:

            if cambios["motivo"] is None:
                raise ValueError(
                    "El motivo no puede ser nulo."
                )

            modelo.motivo = cambios["motivo"]

        # ACTUALIZAR ESTADO
        if "estado" in cambios:

            nuevo_estado = cambios["estado"]

            if nuevo_estado is None:
                raise ValueError(
                    "El estado no puede ser nulo."
                )

            transiciones = {
                EstadoCita.PENDIENTE: {
                    EstadoCita.CONFIRMADA,
                    EstadoCita.CANCELADA,
                },
                EstadoCita.CONFIRMADA: {
                    EstadoCita.CANCELADA,
                    EstadoCita.COMPLETADA,
                },
                EstadoCita.CANCELADA: set(),
                EstadoCita.COMPLETADA: set(),
            }

            actual = modelo.estado

            if (
                nuevo_estado != actual
                and nuevo_estado not in transiciones[actual]
            ):
                raise ValueError(
                    f"No se permite cambiar el estado de "
                    f"'{actual.value}' a '{nuevo_estado.value}'."
                )

            modelo.estado = nuevo_estado

        try:
            self.db.commit()

            actualizada = self._buscar_modelo(modelo.id)

            return self._convertir(actualizada)

        except IntegrityError as error:
            self.db.rollback()

            raise RuntimeError(
                "Conflicto al actualizar la cita."
            ) from error

    def eliminar(self, cita):
        modelo = self._buscar_modelo(cita.id)

        if modelo is None:
            return

        reserva = modelo.reserva

        try:
            self.db.delete(modelo)
            self.db.flush()

            self.db.delete(reserva)
            self.db.commit()

        except IntegrityError as error:
            self.db.rollback()

            raise RuntimeError(
                "No se pudo eliminar la cita y sus servicios asociados."
            ) from error
