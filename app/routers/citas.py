from typing import List
from fastapi import APIRouter, status
from app.schemas import Cita
from app.database import db_citas
from app.routers import citas

router = APIRouter(
    prefix="/citas",
    tags=["Citas"]
)

@router.get("", response_model=List[Cita], status_code=status.HTTP_200_OK)

def listar_citas():
    return db_citas