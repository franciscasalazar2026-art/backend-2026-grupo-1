
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.presentation.dependencies import obtener_servicio_cita
from app.application.services.cita_servicio import (
    CitaServicio,
    CitaNoEncontrada,
)
from app.presentation.schemas.dtos.cita_dto import (
    Cita,
    CitaCreate,
    CitaUpdate,
)
from app.presentation.mappers.cita_response_mapper import (
    CitaResponseMapper,
)
from app.domain.models import EstadoCita


router = APIRouter(prefix="/citas", tags=["Citas"])


@router.get("", response_model=dict)
def listar_citas(
    estado: EstadoCita | None = Query(None),
    ordenar_por: str = Query("fecha_hora"),
    direccion: str = Query("asc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
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
        CitaResponseMapper.a_respuesta(item)
        for item in resultado["items"]
    ]

    return resultado


@router.post(
    "",
    response_model=Cita,
    status_code=status.HTTP_201_CREATED,
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


@router.get("/{cita_id}", response_model=Cita)
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


@router.put("/{cita_id}", response_model=Cita)
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
