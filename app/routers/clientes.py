from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database import get_db
from app.infrastructure.models import ClienteORM
from app.schemas.schemas import Cliente, ClienteCreate, ClienteUpdate, PaginatedResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=PaginatedResponse[Cliente])
def listar_clientes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    consulta = db.query(ClienteORM)
    total = consulta.count()
    clientes = consulta.order_by(ClienteORM.id).offset(offset).limit(limit).all()

    return {
        "items": clientes,
        "total": total,
        "pagina": offset // limit + 1,
        "limite": limit,
        "total_paginas": (total + limit - 1) // limit if total else 1,
    }


@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def crear_cliente(datos: ClienteCreate, db: Session = Depends(get_db)):
    cliente = ClienteORM(**datos.model_dump())
    db.add(cliente)

    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El correo ya está registrado.")


@router.get("/{cliente_id}", response_model=Cliente)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(ClienteORM, cliente_id)

    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    return cliente


@router.put("/{cliente_id}", response_model=Cliente)
def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    db: Session = Depends(get_db),
):
    cliente = db.get(ClienteORM, cliente_id)

    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is None:
            raise HTTPException(status_code=422, detail=f"{campo} no puede ser nulo.")
        setattr(cliente, campo, valor)

    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo actualizar el cliente.")


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(ClienteORM, cliente_id)

    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    db.delete(cliente)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: el cliente tiene reservas asociadas.",
        )
