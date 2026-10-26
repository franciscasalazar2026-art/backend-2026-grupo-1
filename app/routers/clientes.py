from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.schemas import Cliente, ClienteCreate, ClienteUpdate, PaginatedResponse
from app.domain.models import ClienteModel
from app.dependencies import get_db

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("", response_model=PaginatedResponse[Cliente], status_code=status.HTTP_200_OK)
def listar_clientes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    clientes = db.query(ClienteModel).offset(offset).limit(limit).all()
    total = db.query(ClienteModel).count()
    total_paginas = (total + limit - 1) // limit if total > 0 else 1
    pagina = (offset // limit) + 1

    return {
        "items": clientes,
        "total": total,
        "pagina": pagina,
        "limite": limit,
        "total_paginas": total_paginas
    }

@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    existente = db.query(ClienteModel).filter(ClienteModel.email == cliente.email).first()
    if existente:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": "El correo ya está registrado",
                    "details": []
                }
            }
        )
    
    nuevo_cliente = ClienteModel(**cliente.model_dump())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

@router.get("/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"No existe un cliente con el ID {cliente_id}",
                    "details": []
                }
            }
        )
    return cliente

@router.put("/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK)
def actualizar_cliente(cliente_id: int, cliente_data: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"No existe un cliente con el ID {cliente_id}",
                    "details": []
                }
            }
        )
    
    actualizacion = cliente_data.model_dump(exclude_unset=True)
    for key, value in actualizacion.items():
        setattr(cliente, key, value)
    
    db.commit()
    db.refresh(cliente)
    return cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"No existe un cliente con el ID {cliente_id}",
                    "details": []
                }
            }
        )
    
    db.delete(cliente)
    db.commit()
    return None