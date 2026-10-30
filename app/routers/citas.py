from datetime import datetime, timedelta
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.domain.models import EstadoCita
from app.infrastructure.database import get_db
from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    DetalleReservaORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)
from app.schemas.schemas import (
    Cita,
    CitaCreate,
    CitaUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/citas", tags=["Citas"])


def _fecha_a_datetime(valor: str) -> datetime:
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail="La fecha debe tener un formato ISO válido.",
        )

def _validar_fecha_futura(fecha: datetime) -> None:
    ahora = (
        datetime.now(fecha.tzinfo)
        if fecha.tzinfo is not None
        else datetime.now()
    )

    if fecha <= ahora:
        raise HTTPException(
            status_code=422,
            detail="No se puede agendar una cita en el pasado.",
        )

def _opciones_cita():
    ruta_detalles = (
        joinedload(CitaORM.reserva)
        .joinedload(ReservaORM.detalles)
        .joinedload(DetalleReservaORM.profesional_servicio)
    )

    return (
        ruta_detalles.joinedload(ProfesionalServicioORM.profesional),
        ruta_detalles.joinedload(ProfesionalServicioORM.servicio),
    )


def _buscar_cita(db: Session, cita_id: int) -> Optional[CitaORM]:
    consulta = (
        select(CitaORM)
        .options(*_opciones_cita())
        .where(CitaORM.id == cita_id)
    )
    return db.scalars(consulta).unique().first()


def _respuesta_cita(cita: CitaORM) -> dict:
    reserva = cita.reserva
    detalles = sorted(reserva.detalles, key=lambda detalle: detalle.id)

    servicios = []
    for detalle in detalles:
        relacion = detalle.profesional_servicio
        servicio = relacion.servicio
        profesional = relacion.profesional

        servicios.append(
            {
                "servicio_id": servicio.id,
                "servicio_nombre": servicio.nombre,
                "profesional_id": profesional.id,
                "profesional_nombre": profesional.nombre,
                "fecha_hora_inicio": detalle.fecha_hora_inicio.isoformat(),
                "duracion_minutos": detalle.duracion_minutos,
                "precio": detalle.precio,
            }
        )

    return {
        "id": cita.id,
        "cliente_id": reserva.cliente_id,
        "servicio_id": servicios[0]["servicio_id"] if len(servicios) == 1 else None,
        "profesional_id": servicios[0]["profesional_id"] if len(servicios) == 1 else None,
        "fecha_hora": cita.fecha_hora.isoformat(),
        "motivo": cita.motivo,
        "estado": cita.estado,
        "servicios": servicios,
    }


def _esta_cancelada(estado) -> bool:
    valor = str(getattr(estado, "value", estado)).lower()
    return "cancel" in valor or "anulad" in valor


def _tiene_conflicto(
    db: Session,
    profesional_id: int,
    inicio: datetime,
    fin: datetime,
    excluir_cita_id: Optional[int] = None,
) -> bool:
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
        .where(ProfesionalServicioORM.profesional_id == profesional_id)
    )

    for detalle, cita in db.execute(consulta):
        if excluir_cita_id is not None and cita.id == excluir_cita_id:
            continue

        if _esta_cancelada(cita.estado):
            continue

        inicio_existente = detalle.fecha_hora_inicio
        fin_existente = inicio_existente + timedelta(
            minutes=detalle.duracion_minutos
        )

        inicio_nuevo = inicio
        fin_nuevo = fin

        # SQLite puede devolver fechas sin zona horaria.
        if inicio_existente.tzinfo is None and inicio_nuevo.tzinfo is not None:
            inicio_existente = inicio_existente.replace(tzinfo=inicio_nuevo.tzinfo)
            fin_existente = fin_existente.replace(tzinfo=inicio_nuevo.tzinfo)
        elif inicio_existente.tzinfo is not None and inicio_nuevo.tzinfo is None:
            inicio_nuevo = inicio_nuevo.replace(tzinfo=inicio_existente.tzinfo)
            fin_nuevo = fin_nuevo.replace(tzinfo=inicio_existente.tzinfo)

        if inicio_nuevo < fin_existente and inicio_existente < fin_nuevo:
            return True

    return False


@router.get(
    "",
    response_model=PaginatedResponse[Cita],
    status_code=status.HTTP_200_OK,
)
def listar_citas(
    estado: Optional[EstadoCita] = Query(None, description="Filtrar por estado"),
    ordenar_por: str = Query("fecha_hora", pattern="^(id|fecha_hora|estado)$"),
    direccion: str = Query("asc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filtros = []
    if estado is not None:
        filtros.append(CitaORM.estado == estado)

    total = db.scalar(
        select(func.count(CitaORM.id)).where(*filtros)
    ) or 0

    campos_orden = {
        "id": CitaORM.id,
        "fecha_hora": CitaORM.fecha_hora,
        "estado": CitaORM.estado,
    }
    campo = campos_orden[ordenar_por]
    campo = campo.desc() if direccion == "desc" else campo.asc()

    consulta = (
        select(CitaORM)
        .options(*_opciones_cita())
        .where(*filtros)
        .order_by(campo)
        .offset((pagina - 1) * limite)
        .limit(limite)
    )

    citas = db.scalars(consulta).unique().all()

    return {
        "items": [_respuesta_cita(cita) for cita in citas],
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": ceil(total / limite) if total else 1,
    }


@router.post(
    "",
    response_model=Cita,
    status_code=status.HTTP_201_CREATED,
)
def crear_cita(
    datos: CitaCreate,
    db: Session = Depends(get_db),
):
    cliente = db.get(ClienteORM, datos.cliente_id)

    if cliente is None:
        raise HTTPException(
            status_code=400,
            detail=f"El cliente con ID {datos.cliente_id} no existe.",
        )

    if not cliente.activo:
        raise HTTPException(status_code=400, detail="El cliente está inactivo.")

    fecha = _fecha_a_datetime(datos.fecha_hora)
    _validar_fecha_futura(fecha)

    servicios_validados = []
    hora_actual = fecha

    for item in datos.servicios:
        servicio = db.get(ServicioORM, item.servicio_id)
        profesional = db.get(ProfesionalORM, item.profesional_id)

        if servicio is None:
            raise HTTPException(
                status_code=400,
                detail=f"El servicio con ID {item.servicio_id} no existe.",
            )

        if not servicio.activo:
            raise HTTPException(
                status_code=400,
                detail=f"El servicio '{servicio.nombre}' está inactivo.",
            )

        if profesional is None:
            raise HTTPException(
                status_code=400,
                detail=f"El profesional con ID {item.profesional_id} no existe.",
            )

        if not profesional.activo:
            raise HTTPException(
                status_code=400,
                detail=f"El profesional '{profesional.nombre}' está inactivo.",
            )

        relacion = db.scalar(
            select(ProfesionalServicioORM).where(
                ProfesionalServicioORM.profesional_id == profesional.id,
                ProfesionalServicioORM.servicio_id == servicio.id,
            )
        )

        if relacion is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El profesional '{profesional.nombre}' no tiene "
                    f"asociado el servicio '{servicio.nombre}'."
                ),
            )

        fin_servicio = hora_actual + timedelta(
            minutes=servicio.duracion_minutos
        )

        if _tiene_conflicto(
            db,
            profesional.id,
            hora_actual,
            fin_servicio,
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"El profesional '{profesional.nombre}' ya tiene "
                    f"una atención que se cruza con el horario solicitado."
                ),
            )

        servicios_validados.append(
            (relacion, servicio, hora_actual)
        )
        hora_actual = fin_servicio

    try:
        reserva = ReservaORM(cliente_id=cliente.id)
        db.add(reserva)
        db.flush()

        for relacion, servicio, hora_inicio in servicios_validados:
            db.add(
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
            motivo=datos.motivo,
            estado=EstadoCita.PENDIENTE,
        )
        db.add(nueva_cita)
        db.flush()

        nuevo_id = nueva_cita.id
        db.commit()

        cita_guardada = _buscar_cita(db, nuevo_id)
        return _respuesta_cita(cita_guardada)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No fue posible registrar la cita por un conflicto con los datos.",
        )


@router.get(
    "/{cita_id}",
    response_model=Cita,
    status_code=status.HTTP_200_OK,
)
def obtener_cita(
    cita_id: int,
    db: Session = Depends(get_db),
):
    cita = _buscar_cita(db, cita_id)

    if cita is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe una cita con el ID {cita_id}.",
        )

    return _respuesta_cita(cita)


@router.put(
    "/{cita_id}",
    response_model=Cita,
    status_code=status.HTTP_200_OK,
)
def actualizar_cita(
    cita_id: int,
    datos: CitaUpdate,
    db: Session = Depends(get_db),
):
    cita = _buscar_cita(db, cita_id)

    if cita is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe una cita con el ID {cita_id}.",
        )

    cambios = datos.model_dump(exclude_unset=True)

    if "fecha_hora" in cambios:
        if cambios["fecha_hora"] is None:
            raise HTTPException(
                status_code=422,
                detail="La fecha y hora no pueden ser nulas.",
            )

        nueva_fecha = _fecha_a_datetime(cambios["fecha_hora"])
        _validar_fecha_futura(nueva_fecha)

        hora_actual = nueva_fecha
        horarios_propuestos = []

        for detalle in sorted(cita.reserva.detalles, key=lambda d: d.id):
            fin_servicio = hora_actual + timedelta(
                minutes=detalle.duracion_minutos
            )
            profesional_id = detalle.profesional_servicio.profesional_id

            if _tiene_conflicto(
                db,
                profesional_id,
                hora_actual,
                fin_servicio,
                excluir_cita_id=cita.id,
            ):
                raise HTTPException(
                    status_code=409,
                    detail="El nuevo horario entra en conflicto con otra atención.",
                )

            horarios_propuestos.append((detalle, hora_actual))
            hora_actual = fin_servicio

        cita.fecha_hora = nueva_fecha
        for detalle, hora_inicio in horarios_propuestos:
            detalle.fecha_hora_inicio = hora_inicio

    if "motivo" in cambios:
        if cambios["motivo"] is None:
            raise HTTPException(
                status_code=422,
                detail="El motivo no puede ser nulo.",
            )
        cita.motivo = cambios["motivo"]

    if "estado" in cambios:
        if cambios["estado"] is None:
            raise HTTPException(
                status_code=422,
                detail="El estado no puede ser nulo.",
            )

        transiciones_permitidas = {
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

        estado_actual = cita.estado
        estado_nuevo = cambios["estado"]

        if (
            estado_nuevo != estado_actual
            and estado_nuevo not in transiciones_permitidas[estado_actual]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No se permite cambiar el estado de "
                    f"'{estado_actual.value}' a '{estado_nuevo.value}'."
                ),
            )

        cita.estado = estado_nuevo

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar la cita por un conflicto con los datos.",
        )

    cita_actualizada = _buscar_cita(db, cita_id)
    return _respuesta_cita(cita_actualizada)


@router.delete(
    "/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_cita(
    cita_id: int,
    db: Session = Depends(get_db),
):
    cita = _buscar_cita(db, cita_id)

    if cita is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe una cita con el ID {cita_id}.",
        )

    reserva = cita.reserva
    db.delete(cita)
    db.flush()
    db.delete(reserva)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo eliminar la cita y sus servicios asociados.",
        )

    return None