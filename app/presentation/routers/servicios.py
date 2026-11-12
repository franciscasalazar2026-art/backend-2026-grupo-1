
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.presentation.dependencies import obtener_servicio_aplicacion
from app.application.services.servicio_servicio import (
    ServicioAplicacion,
    ServicioNoEncontrado,
)
from app.application.puertos.profesional_repositorio import (
    ConflictoRepositorio,
)
from app.presentation.schemas.dtos.servicio_dto import (
    Servicio,
    ServicioCreate,
    ServicioUpdate,
)
from app.presentation.schemas.dtos.respuesta_paginada import (
    RespuestaPaginada,
)

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get("", response_model=RespuestaPaginada[Servicio])
def listar_servicios(
    buscar: str | None = Query(None),
    solo_activos: bool = Query(True),
    ordenar_por: str = Query("precio"),
    direccion: str = Query("asc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
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
)
def crear_servicio(
    datos: ServicioCreate,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    try:
        return servicio.crear(datos.model_dump())
    except ConflictoRepositorio:
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el servicio por un conflicto con los datos.",
        )


@router.get("/{servicio_id}", response_model=Servicio)
def obtener_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    try:
        return servicio.obtener(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")


@router.put("/{servicio_id}", response_model=Servicio)
def actualizar_servicio(
    servicio_id: int,
    datos: ServicioUpdate,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
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
)
def eliminar_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    try:
        servicio.desactivar(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")


@router.patch("/{servicio_id}/restaurar", response_model=Servicio)
def restaurar_servicio(
    servicio_id: int,
    servicio: ServicioAplicacion = Depends(obtener_servicio_aplicacion),
):
    try:
        return servicio.restaurar(servicio_id)
    except ServicioNoEncontrado:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
