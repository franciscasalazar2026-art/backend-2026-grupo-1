
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models import (
    ProfesionalORM,
    ProfesionalServicioORM,
    ServicioORM,
)
from app.schemas.schemas import (
    Profesional,
    ProfesionalCreate,
    ProfesionalUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/profesionales", tags=["Profesionales"])


@router.get("", response_model=PaginatedResponse[Profesional])
def listar_profesionales(
    buscar: str | None = Query(None),
    solo_activos: bool = Query(True),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    consulta = db.query(ProfesionalORM)

    if solo_activos:
        consulta = consulta.filter(ProfesionalORM.activo.is_(True))

    if buscar:
        consulta = consulta.filter(
            ProfesionalORM.nombre.ilike(f"%{buscar}%")
        )

    total = consulta.count()
    profesionales = (
        consulta.order_by(ProfesionalORM.id)
        .offset((pagina - 1) * limite)
        .limit(limite)
        .all()
    )

    return {
        "items": profesionales,
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": ceil(total / limite) if total else 1,
    }


@router.post(
    "",
    response_model=Profesional,
    status_code=status.HTTP_201_CREATED,
)
def crear_profesional(
    datos: ProfesionalCreate,
    db: Session = Depends(get_db),
):
    profesional = ProfesionalORM(**datos.model_dump())
    db.add(profesional)

    try:
        db.commit()
        db.refresh(profesional)
        return profesional
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El correo del profesional ya está registrado.",
        )


@router.get("/{profesional_id}", response_model=Profesional)
def obtener_profesional(
    profesional_id: int,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    return profesional


@router.put("/{profesional_id}", response_model=Profesional)
def actualizar_profesional(
    profesional_id: int,
    datos: ProfesionalUpdate,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    cambios = datos.model_dump(exclude_unset=True)

    for campo, valor in cambios.items():
        if valor is None:
            raise HTTPException(
                status_code=422,
                detail=f"{campo} no puede ser nulo.",
            )
        setattr(profesional, campo, valor)

    try:
        db.commit()
        db.refresh(profesional)
        return profesional
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar el profesional.",
        )


@router.delete(
    "/{profesional_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_profesional(
    profesional_id: int,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    # Borrado lógico para conservar el historial de citas.
    profesional.activo = False
    db.commit()


@router.patch(
    "/{profesional_id}/restaurar",
    response_model=Profesional,
)
def restaurar_profesional(
    profesional_id: int,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    profesional.activo = True
    db.commit()
    db.refresh(profesional)
    return profesional


@router.get("/{profesional_id}/servicios")
def listar_servicios_profesional(
    profesional_id: int,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")

    return [
        {
            "id": relacion.id,
            "servicio_id": relacion.servicio.id,
            "servicio_nombre": relacion.servicio.nombre,
        }
        for relacion in profesional.profesional_servicios
    ]


@router.post(
    "/{profesional_id}/servicios",
    status_code=status.HTTP_201_CREATED,
)
def asignar_servicio(
    profesional_id: int,
    datos: dict,
    db: Session = Depends(get_db),
):
    profesional = db.get(ProfesionalORM, profesional_id)

    if profesional is None or not profesional.activo:
        raise HTTPException(status_code=404, detail="Profesional no encontrado o inactivo.")

    servicio_id = datos.get("servicio_id")

    if not isinstance(servicio_id, int) or isinstance(servicio_id, bool) or servicio_id <= 0:
        raise HTTPException(status_code=422, detail="servicio_id debe ser un entero positivo.")

    servicio = db.get(ServicioORM, servicio_id)

    if servicio is None or not servicio.activo:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    existente = db.query(ProfesionalServicioORM).filter_by(
        profesional_id=profesional_id,
        servicio_id=servicio_id,
    ).first()

    if existente:
        raise HTTPException(status_code=409, detail="El servicio ya está asignado.")

    asignacion = ProfesionalServicioORM(
        profesional_id=profesional_id,
        servicio_id=servicio_id,
    )

    db.add(asignacion)

    try:
        db.commit()
        db.refresh(asignacion)
        return {
            "id": asignacion.id,
            "profesional_id": profesional_id,
            "servicio_id": servicio_id,
            "servicio_nombre": servicio.nombre,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo asignar el servicio.")
