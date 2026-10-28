from datetime import datetime
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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha debe tener un formato ISO válido.",
        )


def _opciones_cita():
    return (
        joinedload(CitaORM.reserva).joinedload(
            ReservaORM.profesional_servicio
        ),
    )


def _buscar_cita(db: Session, cita_id: int) -> Optional[CitaORM]:
    return db.scalar(
        select(CitaORM)
        .options(*_opciones_cita())
        .where(CitaORM.id == cita_id)
    )


def _respuesta_cita(cita: CitaORM) -> dict:
    reserva = cita.reserva
    profesional_servicio = reserva.profesional_servicio

    return {
        "id": cita.id,
        "cliente_id": reserva.cliente_id,
        "servicio_id": profesional_servicio.servicio_id,
        "profesional_id": profesional_servicio.profesional_id,
        "fecha_hora": cita.fecha_hora.isoformat(),
        "motivo": cita.motivo,
        "estado": cita.estado,
    }


@router.get(
    "",
    response_model=PaginatedResponse[Cita],
    status_code=status.HTTP_200_OK,
)
def listar_citas(
    estado: Optional[EstadoCita] = Query(
        None, description="Filtrar por estado"
    ),
    ordenar_por: str = Query(
        "fecha_hora",
        pattern="^(id|fecha_hora|estado)$",
    ),
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
        raise HTTPException(
            status_code=400,
            detail="El cliente está inactivo.",
        )

    profesional = db.get(ProfesionalORM, datos.profesional_id)
    if profesional is None:
        raise HTTPException(
            status_code=400,
            detail="El profesional indicado no existe.",
        )
    if not profesional.activo:
        raise HTTPException(
            status_code=400,
            detail="El profesional está inactivo.",
        )

    servicio = db.get(ServicioORM, datos.servicio_id)
    if servicio is None:
        raise HTTPException(
            status_code=400,
            detail="El servicio indicado no existe.",
        )
    if not servicio.activo:
        raise HTTPException(
            status_code=400,
            detail="El servicio está inactivo.",
        )

    relacion = db.scalar(
        select(ProfesionalServicioORM).where(
            ProfesionalServicioORM.profesional_id
            == datos.profesional_id,
            ProfesionalServicioORM.servicio_id == datos.servicio_id,
        )
    )

    if relacion is None:
        raise HTTPException(
            status_code=400,
            detail="El profesional no tiene asociado ese servicio.",
        )

    fecha = _fecha_a_datetime(datos.fecha_hora)

    try:
        reserva = ReservaORM(
            cliente_id=cliente.id,
            profesional_servicio_id=relacion.id,
        )
        db.add(reserva)
        db.flush()

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
            detail="No fue posible registrar la cita por una restricción de la base de datos.",
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
        cita.fecha_hora = _fecha_a_datetime(cambios["fecha_hora"])

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
        cita.estado = cambios["estado"]

    db.commit()

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

    # Elimina ambos registros para no dejar una reserva huérfana.
    db.delete(cita)
    db.flush()
    db.delete(reserva)
    db.commit()

    return None
