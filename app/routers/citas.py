from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import Cita, CitaCreate
from app.database import db_clientes, db_citas
from app.models import EstadoCita


router = APIRouter(
    prefix="/citas",
    tags=["Citas"]
)


@router.get(
    "",
    response_model=List[Cita],
    status_code=status.HTTP_200_OK
)
def listar_citas(
    estado: Optional[EstadoCita] = Query(
        None,
        description="Filtrar citas por estado"
    ),
    ordenar_fecha: Optional[str] = Query(
        None,
        pattern="^(asc|desc)$",
        description="Ordenar citas por fecha: asc o desc"
    )
):
    resultado = db_citas

    if estado:
        resultado = [c for c in resultado if c.estado == estado]

    if ordenar_fecha == "asc":
        resultado = sorted(resultado, key=lambda c: c.fecha_hora)
    elif ordenar_fecha == "desc":
        resultado = sorted(resultado, key=lambda c: c.fecha_hora, reverse=True)

    return resultado


@router.post(
    "",
    response_model=Cita,
    status_code=status.HTTP_201_CREATED
)
def crear_cita(cita: CitaCreate):
    if not any(c.id == cita.cliente_id for c in db_clientes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del cliente no existe"
        )

    nuevo_id = max([c.id for c in db_citas], default=0) + 1
    nueva_cita = Cita(id=nuevo_id, **cita.model_dump())
    db_citas.append(nueva_cita)

    return nueva_cita