from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.puertos.profesional_repositorio import ConflictoRepositorio
from app.application.services.cliente_servicio import (
    ClienteNoEncontrado,
    ClienteServicio,
)
from app.infrastructure.models.usuario import UsuarioORM
from app.presentation.dependencies import (
    get_current_user,
    obtener_servicio_cliente,
    require_role,
)
from app.presentation.schemas.dtos.cliente_dto import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
)
from app.presentation.schemas.dtos.respuesta_paginada import RespuestaPaginada

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get(
    "",
    response_model=RespuestaPaginada[Cliente],
    summary="Listar clientes paginados",
    responses={401: {"description": "Credenciales ausentes o inválidas"}},
    description="Obtiene el listado paginado de clientes registrados. Requiere estar autenticado.",
)
def listar_clientes(
    limit: int = Query(
        10, ge=1, le=100, description="Cantidad máxima de registros por página"
    ),
    offset: int = Query(
        0, ge=0, description="Cantidad de registros a omitir desde el inicio"
    ),
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
    _: UsuarioORM = Depends(get_current_user),
):
    return servicio.listar(limite=limit, desplazamiento=offset)


@router.post(
    "",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo cliente",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Rol sin permiso"},
        409: {"description": "Correo duplicado"},
    },
    description="Crea un nuevo cliente validando unicidad de correo. Requiere rol admin o recepcionista.",
)
def crear_cliente(
    datos: ClienteCreate,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
    _: UsuarioORM = Depends(require_role("admin", "recepcionista")),
):
    try:
        return servicio.crear(datos.model_dump())
    except ConflictoRepositorio:
        raise HTTPException(409, detail="El correo ya está registrado.")


@router.get(
    "/{cliente_id}",
    response_model=Cliente,
    summary="Consultar cliente por ID",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        404: {"description": "Cliente no encontrado"},
    },
    description="Obtiene los datos de un cliente específico mediante su identificador. Requiere autenticación.",
)
def obtener_cliente(
    cliente_id: int,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
    _: UsuarioORM = Depends(get_current_user),
):
    try:
        return servicio.obtener(cliente_id)
    except ClienteNoEncontrado:
        raise HTTPException(404, detail="Cliente no encontrado.")


@router.put(
    "/{cliente_id}",
    response_model=Cliente,
    summary="Actualizar datos de un cliente",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Rol sin permiso"},
        404: {"description": "Cliente no encontrado"},
        409: {"description": "Conflicto al actualizar los datos"},
    },
    description="Modifica los datos de un cliente existente. Requiere rol admin o recepcionista.",
)
def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
    _: UsuarioORM = Depends(require_role("admin", "recepcionista")),
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


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un cliente",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Rol sin permiso"},
        404: {"description": "Cliente no encontrado"},
        409: {"description": "El cliente tiene reservas asociadas"},
    },
    description="Elimina un cliente si no tiene reservas asociadas. Requiere rol admin o recepcionista.",
)
def eliminar_cliente(
    cliente_id: int,
    servicio: ClienteServicio = Depends(obtener_servicio_cliente),
    _: UsuarioORM = Depends(require_role("admin", "recepcionista")),
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
