from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.profesional_servicio import (
    ProfesionalInactivo,
    ProfesionalNoEncontrado,
    ServicioNoEncontrado,
    ServicioProfesional,
)
from app.presentation.dependencies import obtener_servicio_profesional
from app.presentation.schemas.dtos.profesional_dto import (
    Profesional,
    ProfesionalCreate,
    ProfesionalUpdate,
)
from app.presentation.schemas.dtos.respuesta_paginada import (
    RespuestaPaginada,
)

router = APIRouter(
    prefix="/profesionales",
    tags=["Profesionales"],
)


@router.get(
    "",
    response_model=RespuestaPaginada[Profesional],
    summary="Listar profesionales paginados",
    description="Obtiene un listado paginado de profesionales con búsqueda por nombre o especialidad y filtro de activos.",
)
def listar_profesionales(
    buscar: str | None = Query(None, description="Texto a buscar en nombre o especialidad"),
    solo_activos: bool = Query(True, description="Si es verdadero, retorna únicamente profesionales activos"),
    pagina: int = Query(1, ge=1, description="Número de página (inicia en 1)"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad de elementos por página"),
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    return servicio.listar(
        buscar=buscar,
        solo_activos=solo_activos,
        pagina=pagina,
        limite=limite,
    )


@router.post(
    "",
    response_model=Profesional,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo profesional",
    responses={409: {"description": "Correo electrónico ya registrado o conflicto de datos"}},
    description="Crea un nuevo profesional en el sistema.",
)
def crear_profesional(
    datos: ProfesionalCreate,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.crear(datos.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.get(
    "/{profesional_id}",
    response_model=Profesional,
    summary="Obtener detalle de un profesional",
    responses={404: {"description": "Profesional no encontrado"}},
    description="Consulta los datos de un profesional específico por su ID.",
)
def obtener_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.obtener(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.put(
    "/{profesional_id}",
    response_model=Profesional,
    summary="Actualizar un profesional",
    responses={
        404: {"description": "Profesional no encontrado"},
        409: {"description": "Conflicto de datos al actualizar"},
    },
    description="Actualiza los datos de un profesional existente.",
)
def actualizar_profesional(
    profesional_id: int,
    datos: ProfesionalUpdate,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.actualizar(
            profesional_id,
            datos.model_dump(exclude_unset=True),
        )
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")
    except ValueError as error:
        codigo = 409 if "No se pudo actualizar" in str(error) else 422
        raise HTTPException(status_code=codigo, detail=str(error))


@router.delete(
    "/{profesional_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar un profesional",
    responses={404: {"description": "Profesional no encontrado"}},
    description="Realiza un borrado lógico del profesional marcándolo como inactivo.",
)
def eliminar_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        servicio.desactivar(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.patch(
    "/{profesional_id}/restaurar",
    response_model=Profesional,
    summary="Restaurar un profesional desactivado",
    responses={404: {"description": "Profesional no encontrado"}},
    description="Reactiva un profesional previamente desactivado.",
)
def restaurar_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.restaurar(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.get(
    "/{profesional_id}/servicios",
    summary="Listar servicios asignados a un profesional",
    responses={404: {"description": "Profesional no encontrado"}},
    description="Obtiene el listado de servicios habilitados para un profesional específico.",
)
def listar_servicios_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.listar_servicios(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.post(
    "/{profesional_id}/servicios",
    status_code=status.HTTP_201_CREATED,
    summary="Asignar un servicio a un profesional",
    responses={
        404: {"description": "Profesional o servicio no encontrado o inactivo"},
        409: {"description": "El servicio ya estaba asignado al profesional"},
    },
    description="Asocia un servicio activo del catálogo a un profesional activo.",
)
def asignar_servicio(
    profesional_id: int,
    datos: dict,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        servicio_id = datos.get("servicio_id")

        return servicio.asignar_servicio(
            profesional_id,
            servicio_id,
        )

    except ProfesionalNoEncontrado:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )
    except ProfesionalInactivo:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado o inactivo.",
        )
    except ServicioNoEncontrado:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado o inactivo.",
        )
    except ValueError as error:
        mensaje = str(error)
        codigo = 409 if "ya está asignado" in mensaje else 422
        raise HTTPException(status_code=codigo, detail=mensaje)
