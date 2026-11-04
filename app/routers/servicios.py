from math import ceil
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models import ServicioORM
from app.schemas.schemas import ServicioCreate, ServicioUpdate, ServicioResponse

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("", summary="Listar servicios con filtrado, ordenamiento y paginación")
def listar_servicios(
    buscar: Optional[str] = Query(None, description="Buscar servicio por coincidencia en el nombre"),
    solo_activos: bool = Query(True, description="Filtrar solo los servicios activos"),
    ordenar_por: str = Query("precio", description="Campo por el cual ordenar (nombre, precio, id)"),
    direccion: str = Query("asc", regex="^(asc|desc)$", description="Dirección del ordenamiento"),
    pagina: int = Query(1, ge=1, description="Número de página (inicia en 1)"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad máxima de registros por página"),
    db: Session = Depends(get_db),
):
    """Consulta la lista de servicios aplicando filtrado, ordenamiento y paginación estructurada."""
    # 1. Filtrado
    consulta = db.query(ServicioORM)

    if solo_activos:
        consulta = consulta.filter(ServicioORM.activo == True)

    if buscar:
        consulta = consulta.filter(ServicioORM.nombre.ilike(f"%{buscar}%"))

    total = consulta.count()

    # 2. Ordenamiento
    campo_orden = getattr(ServicioORM, ordenar_por, ServicioORM.precio)
    if direccion.lower() == "desc":
        consulta = consulta.order_by(campo_orden.desc())
    else:
        consulta = consulta.order_by(campo_orden.asc())

    # 3. Paginación
    offset = (pagina - 1) * limite
    items = consulta.offset(offset).limit(limite).all()
    total_paginas = ceil(total / limite) if total > 0 else 1

    return {
        "items": [ServicioResponse.model_validate(item) for item in items],
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": total_paginas,
    }


@router.post(
    "",
    response_model=ServicioResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Conflicto al registrar el servicio."}},
)
def crear_servicio(
    datos: ServicioCreate,
    db: Session = Depends(get_db),
):
    servicio = ServicioORM(**datos.model_dump())
    db.add(servicio)

    try:
        db.commit()
        db.refresh(servicio)
        return servicio
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SERVICE_CONFLICT",
                "message": "No se pudo registrar el servicio por un conflicto con los datos.",
                "details": [],
            },
        )


@router.get(
    "/{servicio_id}",
    response_model=ServicioResponse,
    responses={404: {"description": "Servicio no encontrado."}},
)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Consulta un servicio específico del catálogo por su ID."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": f"Servicio con ID {servicio_id} no encontrado.",
                "details": [],
            },
        )
    return servicio


@router.put(
    "/{servicio_id}",
    response_model=ServicioResponse,
    responses={
        404: {"description": "Servicio no encontrado."},
        409: {"description": "Conflicto al actualizar el servicio."},
    },
)
def actualizar_servicio(
    servicio_id: int,
    datos: ServicioUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza la información parcial o total de un servicio existente."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": f"Servicio con ID {servicio_id} no encontrado.",
                "details": [],
            },
        )

    datos_actualizacion = datos.model_dump(exclude_unset=True)
    for clave, valor in datos_actualizacion.items():
        setattr(servicio, clave, valor)

    try:
        db.commit()
        db.refresh(servicio)
        return servicio
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "UPDATE_CONFLICT",
                "message": "Error de integridad al actualizar el servicio.",
                "details": [],
            },
        )


@router.delete(
    "/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Servicio no encontrado."}},
)
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Desactiva un servicio (borrado lógico) para preservar el historial de citas."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": f"Servicio con ID {servicio_id} no encontrado.",
                "details": [],
            },
        )

    servicio.activo = False
    db.commit()
    return None


@router.patch(
    "/{servicio_id}/restaurar",
    response_model=ServicioResponse,
    responses={404: {"description": "Servicio no encontrado."}},
)
def restaurar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Reactiva un servicio que fue desactivado previamente mediante borrado lógico."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_FOUND",
                "message": f"Servicio con ID {servicio_id} no encontrado.",
                "details": [],
            },
        )

    servicio.activo = True
    db.commit()
    db.refresh(servicio)
    return servicio
