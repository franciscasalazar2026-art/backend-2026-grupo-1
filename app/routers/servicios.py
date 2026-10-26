from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Servicio
from app.schemas import ServicioCreate, ServicioResponse

router = APIRouter(prefix="/servicios", tags=["Servicios"])

@router.get("/", response_model=list[ServicioResponse])
def listar_servicios(db: Session = Depends(get_db)):
    return db.query(Servicio).all()

@router.post("/", response_model=ServicioResponse, status_code=status.HTTP_201_CREATED)
def crear_servicio(servicio: ServicioCreate, db: Session = Depends(get_db)):
    nuevo_servicio = Servicio(**servicio.model_dump())
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio
