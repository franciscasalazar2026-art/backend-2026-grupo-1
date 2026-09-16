import math
from typing import Optional
from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from app.schemas.schemas import Cita, CitaCreate, CitaUpdate, PaginatedResponse
from app.domain.models import EstadoCita
from app.repositories.database import db_citas, db_clientes

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.get("", response_model=PaginatedResponse[Cita], status_code=status.HTTP_200_OK)
def listar_citas(
    estado: Optional[EstadoCita] = Query(None, description="Filtrar por estado"),
    ordenar_por: str = Query("fecha_hora", description="Atributo para ordenar"),
    direccion: str = Query("asc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    resultado = db_citas
    
    # 1. FILTRAR
    if estado:
        resultado = [c for c in resultado if c.estado == estado]
        
    # 2. ORDENAR
    reverse = (direccion == "desc")
    if hasattr(Cita, ordenar_por):
        resultado = sorted(resultado, key=lambda x: getattr(x, ordenar_por), reverse=reverse)
        
    # 3. PAGINAR
    total = len(resultado)
    total_paginas = math.ceil(total / limite) if total > 0 else 1
    offset = (pagina - 1) * limite
    items = resultado[offset : offset + limite]
    
    return {
        "items": items,
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": total_paginas
    }

@router.post("", response_model=Cita, status_code=status.HTTP_201_CREATED)
def crear_cita(cita: CitaCreate):
    if not any(c.id == cita.cliente_id for c in db_clientes):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_RELATION",
                    "message": f"El cliente con ID {cita.cliente_id} no existe",
                    "details": []
                }
            }
        )
        
    nuevo_id = max([c.id for c in db_citas], default=0) + 1
    nueva_cita = Cita(id=nuevo_id, estado=EstadoCita.PENDIENTE, **cita.model_dump())
    db_citas.append(nueva_cita)
    return nueva_cita

@router.get("/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK)
def obtener_cita(cita_id: int):
    for c in db_citas:
        if c.id == cita_id:
            return c
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )

@router.put("/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK)
def actualizar_cita(cita_id: int, cita_data: CitaUpdate):
    for idx, c in enumerate(db_citas):
        if c.id == cita_id:
            datos = c.model_dump()
            actualizacion = cita_data.model_dump(exclude_unset=True)
            datos.update(actualizacion)
            
            cita_modificada = Cita(**datos)
            db_citas[idx] = cita_modificada
            return cita_modificada
            
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )

@router.delete("/{cita_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cita(cita_id: int):
    for idx, c in enumerate(db_citas):
        if c.id == cita_id:
            db_citas.pop(idx)
            return None
            
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )