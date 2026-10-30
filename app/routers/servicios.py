from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models import ServicioORM
from app.schemas.schemas import ServicioCreate, ServicioUpdate, ServicioResponse
router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("", response_model=list[ServicioResponse])
def listar_servicios(
    buscar: Optional[str] = Query(None, description="Buscar servicio por coincidencia en el nombre"),
    solo_activos: bool = Query(True, description="Filtrar solo los servicios activos"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad máxima de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir para paginación"),
    db: Session = Depends(get_db),
):
    """Consulta la lista de servicios con soporte para paginación y búsqueda por nombre."""
    consulta = db.query(ServicioORM)

    if solo_activos:
        consulta = consulta.filter(ServicioORM.activo == True)

    if buscar:
        consulta = consulta.filter(ServicioORM.nombre.ilike(f"%{buscar}%"))

    return consulta.order_by(ServicioORM.id).offset(offset).limit(limite).all()


@router.post(
    "",
    response_model=ServicioResponse,
    status_code=status.HTTP_201_CREATED,
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
            detail="No se pudo registrar el servicio por un conflicto con los datos.",
        )
@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Consulta un servicio específico del catálogo por su ID."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio con ID {servicio_id} no encontrado.",
        )
    return servicio


@router.put("/{servicio_id}", response_model=ServicioResponse)
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
            detail=f"Servicio con ID {servicio_id} no encontrado.",
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
            detail="Error de integridad al actualizar el servicio.",
        )


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Desactiva un servicio (borrado lógico) para preservar el historial de citas."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio con ID {servicio_id} no encontrado.",
        )

    servicio.activo = False
    db.commit()
    return None

@router.patch("/{servicio_id}/restaurar", response_model=ServicioResponse)
def restaurar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    """Reactiva un servicio que fue desactivado previamente mediante borrado lógico."""
    servicio = db.query(ServicioORM).filter(ServicioORM.id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio con ID {servicio_id} no encontrado.",
        )

    servicio.activo = True
    db.commit()
    db.refresh(servicio)
    return servicio
