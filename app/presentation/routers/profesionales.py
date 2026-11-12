
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.presentation.dependencies import obtener_servicio_profesional
from app.application.services.profesional_servicio import (
    ServicioProfesional,
    ProfesionalNoEncontrado,
    ProfesionalInactivo,
    ServicioNoEncontrado,
)
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


@router.get("", response_model=RespuestaPaginada[Profesional])
def listar_profesionales(
    buscar: str | None = Query(None),
    solo_activos: bool = Query(True),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
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
)
def crear_profesional(
    datos: ProfesionalCreate,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.crear(datos.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.get("/{profesional_id}", response_model=Profesional)
def obtener_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.obtener(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.put("/{profesional_id}", response_model=Profesional)
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
)
def restaurar_profesional(
    profesional_id: int,
    servicio: ServicioProfesional = Depends(obtener_servicio_profesional),
):
    try:
        return servicio.restaurar(profesional_id)
    except ProfesionalNoEncontrado:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")


@router.get("/{profesional_id}/servicios")
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
