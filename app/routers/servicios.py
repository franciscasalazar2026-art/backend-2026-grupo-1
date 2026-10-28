from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models import ServicioORM
from app.schemas.schemas import ServicioCreate, ServicioResponse

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("", response_model=list[ServicioResponse])
def listar_servicios(db: Session = Depends(get_db)):
    return db.query(ServicioORM).order_by(ServicioORM.id).all()


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
