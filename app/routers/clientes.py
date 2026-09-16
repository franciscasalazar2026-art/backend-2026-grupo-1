from typing import List
from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from app.schemas.schemas import Cliente, ClienteCreate, ClienteUpdate
from app.repositories.database import db_clientes

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("", response_model=List[Cliente], status_code=status.HTTP_200_OK)
def listar_clientes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return db_clientes[offset : offset + limit]

@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente: ClienteCreate):
    for c in db_clientes:
        if c.email == cliente.email:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": {
                        "code": "EMAIL_ALREADY_EXISTS",
                        "message": "El correo ya esta registrado",
                        "details": []
                    }
                }
            )
            
    nuevo_id = max([c.id for c in db_clientes], default=0) + 1
    nuevo_cliente = Cliente(id=nuevo_id, activo=True, **cliente.model_dump())
    db_clientes.append(nuevo_cliente)
    return nuevo_cliente

@router.get("/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK)
def obtener_cliente(cliente_id: int):
    for c in db_clientes:
        if c.id == cliente_id:
            return c
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

@router.put("/{cliente_id}", response_model=Cliente, status_code=status.HTTP_200_OK)
def actualizar_cliente(cliente_id: int, cliente_data: ClienteUpdate):
    for idx, c in enumerate(db_clientes):
        if c.id == cliente_id:
            datos = c.model_dump()
            actualizacion = cliente_data.model_dump(exclude_unset=True)
            datos.update(actualizacion)
            
            cliente_modificado = Cliente(**datos)
            db_clientes[idx] = cliente_modificado
            return cliente_modificado
            
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

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int):
    for idx, c in enumerate(db_clientes):
        if c.id == cliente_id:
            db_clientes.pop(idx)
            return None
            
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