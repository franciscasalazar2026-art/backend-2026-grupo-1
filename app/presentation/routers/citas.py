from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.cita_servicio import (
    CitaNoEncontrada,
    CitaServicio,
)
from app.domain.models import EstadoCita
from app.presentation.dependencies import obtener_servicio_cita
from app.presentation.mappers.cita_response_mapper import (
    CitaResponseMapper,
)
from app.presentation.schemas.dtos.cita_dto import (
    Cita,
    CitaCreate,
    CitaUpdate,
)
from app.presentation.schemas.dtos.respuesta_paginada import RespuestaPaginada

router = APIRouter(prefix="/citas", tags=["Citas"])


@router.get(
    "",
    response_model=RespuestaPaginada[Cita],
    summary="Listar citas paginadas",
    description="Obtiene un listado paginado de citas con filtro opcional por estado y ordenamiento validado.",
)
def listar_citas(
    estado: EstadoCita | None = Query(None, description="Filtrar por estado de la cita"),
    ordenar_por: str = Query("fecha_hora", description="Campo de ordenamiento: fecha_hora, id o estado"),
    direccion: str = Query("asc", pattern="^(asc|desc)$", description="Dirección: asc o desc"),
    pagina: int = Query(1, ge=1, description="Número de página (inicia en 1)"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad de elementos por página"),
    servicio: CitaServicio = Depends(obtener_servicio_cita),
):
    if ordenar_por not in {"fecha_hora", "id", "estado"}:
        raise HTTPException(
            status_code=422,
            detail="Campo de ordenamiento no válido.",
        )

    resultado = servicio.listar(
        estado=estado,
        ordenar_por=ordenar_por,
        direccion=direccion,
        pagina=pagina,
        limite=limite,
    )

    resultado["items"] = [
        CitaResponseMapper.a_respuesta(item) for item in resultado["items"]
    ]

    return resultado


@router.post(
    "",
    response_model=Cita,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una nueva cita",
    responses={409: {"description": "Conflicto de agenda o de persistencia"}},
    description="Crea una reserva con uno o más servicios y registra la cita asociada validando disponibilidad horaria.",
)
def crear_cita(
    datos: CitaCreate,
    servicio: CitaServicio = Depends(obtener_servicio_cita),
):
    try:
        resultado = servicio.crear(datos.model_dump())
        return CitaResponseMapper.a_respuesta(resultado)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )


@router.get(
    "/{cita_id}",
    response_model=Cita,
    summary="Obtener detalle de una cita",
    responses={404: {"description": "Cita no encontrada"}},
    description="Consulta los datos completos de una cita específica junto con el detalle de sus servicios agendados.",
)
def obtener_cita(
    cita_id: int,
    servicio: CitaServicio = Depends(obtener_servicio_cita),
):
    try:
        resultado = servicio.obtener(cita_id)
        return CitaResponseMapper.a_respuesta(resultado)

    except CitaNoEncontrada:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )


@router.put(
    "/{cita_id}",
    response_model=Cita,
    summary="Actualizar una cita",
    responses={
        404: {"description": "Cita no encontrada"},
        409: {"description": "Conflicto de agenda o de persistencia"},
    },
    description="Modifica fecha, hora, motivo o estado de una cita existente verificando que no existan solapamientos.",
)
def actualizar_cita(
    cita_id: int,
    datos: CitaUpdate,
    servicio: CitaServicio = Depends(obtener_servicio_cita),
):
    try:
        resultado = servicio.actualizar(
            cita_id,
            datos.model_dump(exclude_unset=True),
        )

        return CitaResponseMapper.a_respuesta(resultado)

    except CitaNoEncontrada:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )


@router.delete(
    "/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cita",
    responses={
        404: {"description": "Cita no encontrada"},
        409: {"description": "Conflicto al eliminar la cita"},
    },
    description="Elimina una cita existente y su reserva asociada del sistema.",
)
def eliminar_cita(
    cita_id: int,
    servicio: CitaServicio = Depends(obtener_servicio_cita),
):
    try:
        servicio.eliminar(cita_id)

    except CitaNoEncontrada:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )
