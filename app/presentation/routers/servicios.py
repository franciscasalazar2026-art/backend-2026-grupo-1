from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.puertos.profesional_repositorio import ConflictoRepositorio
from app.application.services.servicio_servicio import (
    ServicioAplicacion,
    ServicioNoEncontrado,
)
from app.infrastructure.models.usuario import UsuarioORM
from app.presentation.dependencies import (
    obtener_servicio_aplicacion,
    require_role,
)
from app.presentation.schemas.dtos.respuesta_paginada import RespuestaPaginada
from app.presentation.schemas.dtos.servicio_dto import (
    Servicio,
    ServicioCreate,
    ServicioUpdate,
)

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get(
    "",
    response_model=RespuestaPaginada[Servicio],
    summary="Listar servicios paginados",
    description="Obtiene un listado paginado de servicios con búsqueda por texto, filtro de activos y ordenamiento validado.",
)
def listar_servicios(
    buscar: str | None = Query(
        None, description="Texto a buscar en nombre o descripción del servicio"
    ),
    solo_activos: bool = Query(
        True, description="Si es verdadero, retorna únicamente servicios activos"
    ),
    ordenar_por: str = Query(
        "precio", description="Campo de ordenamiento permitido: nombre, precio o id"
    ),
    direccion: str = Query(
        "asc",
        pattern="^(asc|desc)$",
        description="Dirección del ordenamiento: asc o desc",
    ),
    pagina: int = Query(1, ge=1, description="Número de página (inicia en 1)"),
    limite: int = Query(
        10, ge=1, le=100, description="Cantidad de elementos por página"
    ),
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    if ordenar_por not in {"nombre", "precio", "id"}:
        raise HTTPException(
            status_code=422,
            detail="El campo de ordenamiento debe ser nombre, precio o id.",
        )

    return servicio.listar(
        buscar=buscar,
        solo_activos=solo_activos,
        ordenar_por=ordenar_por,
        direccion=direccion,
        pagina=pagina,
        limite=limite,
    )


@router.post(
    "",
    response_model=Servicio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo servicio",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Se requiere rol admin"},
        409: {"description": "Conflicto al crear el servicio"},
    },
    description="Registra un nuevo servicio en el catálogo. Requiere autenticación con rol admin.",
)
def crear_servicio(
    datos: ServicioCreate,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
    _: UsuarioORM = Depends(require_role("admin")),
):
    try:
        return servicio.crear(datos.model_dump())
    except ConflictoRepositorio:
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el servicio por un conflicto con los datos.",
        )


@router.get(
    "/{servicio_id}",
    response_model=Servicio,
    summary="Obtener detalle de un servicio",
    responses={404: {"description": "Servicio no encontrado"}},
    description="Consulta la información completa de un servicio específico mediante su ID.",
)
def obtener_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    try:
        return servicio.obtener(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")


@router.put(
    "/{servicio_id}",
    response_model=Servicio,
    summary="Actualizar un servicio",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Servicio no encontrado"},
        409: {"description": "Conflicto al actualizar el servicio"},
    },
    description="Modifica los datos de un servicio existente. Requiere autenticación con rol admin.",
)
def actualizar_servicio(
    servicio_id: int,
    datos: ServicioUpdate,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
    _: UsuarioORM = Depends(require_role("admin")),
):
    try:
        return servicio.actualizar(
            servicio_id,
            datos.model_dump(exclude_unset=True),
        )
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    except ConflictoRepositorio:
        raise HTTPException(status_code=409, detail="Error al actualizar el servicio.")
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.delete(
    "/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar un servicio",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Servicio no encontrado"},
    },
    description="Realiza un borrado lógico del servicio marcándolo como inactivo. Requiere rol admin.",
)
def eliminar_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
    _: UsuarioORM = Depends(require_role("admin")),
):
    try:
        servicio.desactivar(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")


@router.patch(
    "/{servicio_id}/restaurar",
    response_model=Servicio,
    summary="Restaurar un servicio desactivado",
    responses={
        401: {"description": "Credenciales ausentes o inválidas"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Servicio no encontrado"},
    },
    description="Reactiva un servicio previamente desactivado. Requiere autenticación con rol admin.",
)
def restaurar_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
    _: UsuarioORM = Depends(require_role("admin")),
):
    try:
        return servicio.restaurar(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
