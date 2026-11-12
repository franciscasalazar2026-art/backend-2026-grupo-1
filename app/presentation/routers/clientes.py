
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.presentation.dependencies import obtener_servicio_cliente
from app.application.services.cliente_servicio import (
    ClienteServicio,
    ClienteNoEncontrado,
)
from app.application.puertos.profesional_repositorio import (
    ConflictoRepositorio,
)
from app.presentation.schemas.dtos.cliente_dto import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
)
from app.presentation.schemas.dtos.respuesta_paginada import (
    RespuestaPaginada,
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=RespuestaPaginada[Cliente])
def listar_clientes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
):
    return servicio.listar(limite=limit, desplazamiento=offset)


@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    datos: ClienteCreate,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
):
    try:
        return servicio.crear(datos.model_dump())
    except ConflictoRepositorio:
        raise HTTPException(409, detail="El correo ya está registrado.")


@router.get("/{cliente_id}", response_model=Cliente)
def obtener_cliente(
    cliente_id: int,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
):
    try:
        return servicio.obtener(cliente_id)
    except ClienteNoEncontrado:
        raise HTTPException(404, detail="Cliente no encontrado.")


@router.put("/{cliente_id}", response_model=Cliente)
def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
):
    try:
        return servicio.actualizar(
            cliente_id,
            datos.model_dump(exclude_unset=True),
        )
    except ClienteNoEncontrado:
        raise HTTPException(404, detail="Cliente no encontrado.")
    except ConflictoRepositorio:
        raise HTTPException(409, detail="No se pudo actualizar el cliente.")
    except ValueError as error:
        raise HTTPException(422, detail=str(error))


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(
    cliente_id: int,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
):
    try:
        servicio.eliminar(cliente_id)
    except ClienteNoEncontrado:
        raise HTTPException(404, detail="Cliente no encontrado.")
    except ConflictoRepositorio:
        raise HTTPException(
            409,
            detail="No se puede eliminar: el cliente tiene reservas asociadas.",
        )
