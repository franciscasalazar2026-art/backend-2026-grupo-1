import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.domain.models import EstadoCita
from app.repositories.database import db_citas, db_clientes
from app.schemas.schemas import Cita, CitaCreate, CitaUpdate, PaginatedResponse


router = APIRouter(prefix="/citas", tags=["Citas"])


@router.get(
    "",
    response_model=PaginatedResponse[Cita],
    status_code=status.HTTP_200_OK
)
def listar_citas(
    estado: Optional[EstadoCita] = Query(None, description="Filtrar por estado"),
    ordenar_por: str = Query("fecha_hora", description="Atributo para ordenar"),
    direccion: str = Query("asc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    resultado = db_citas

    if estado:
        resultado = [c for c in resultado if c.estado == estado]

    campos_ordenables = {
        "id",
        "fecha_hora",
        "cliente_id",
        "servicio_id",
        "profesional_id",
        "estado"
    }

    if ordenar_por not in campos_ordenables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede ordenar por el campo '{ordenar_por}'"
        )

    reverse = direccion == "desc"
    resultado = sorted(
        resultado,
        key=lambda cita: getattr(cita, ordenar_por),
        reverse=reverse
    )

    total = len(resultado)
    total_paginas = math.ceil(total / limite) if total > 0 else 1
    offset = (pagina - 1) * limite
    items = resultado[offset:offset + limite]

    return {
        "items": items,
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": total_paginas
    }


@router.post("", response_model=Cita, status_code=status.HTTP_201_CREATED)
def crear_cita(cita: CitaCreate):
    try:
        fecha_hora = datetime.fromisoformat(cita.fecha_hora)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha y hora deben tener formato ISO 8601"
        ) from exc

    ahora = datetime.now(fecha_hora.tzinfo)
    if fecha_hora <= ahora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede agendar una cita en el pasado"
        )

    if not any(cliente.id == cita.cliente_id for cliente in db_clientes):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_RELATION",
                    "message": f"El cliente con ID {cita.cliente_id} no existe",
                    "details": []
                }
            }
        )

    nuevo_id = max([c.id for c in db_citas], default=0) + 1
    nueva_cita = Cita(
        id=nuevo_id,
        estado=EstadoCita.PENDIENTE,
        **cita.model_dump()
    )
    db_citas.append(nueva_cita)
    return nueva_cita


@router.get("/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK)
def obtener_cita(cita_id: int):
    for cita in db_citas:
        if cita.id == cita_id:
            return cita
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )


@router.put("/{cita_id}", response_model=Cita, status_code=status.HTTP_200_OK)
def actualizar_cita(cita_id: int, cita_data: CitaUpdate):
    for idx, cita in enumerate(db_citas):
        if cita.id == cita_id:
            datos = cita.model_dump()
            actualizacion = cita_data.model_dump(exclude_unset=True)
            if "estado" in actualizacion and actualizacion["estado"] is not None:
                estado_actual = cita.estado
                estado_nuevo = actualizacion["estado"]

                transiciones_permitidas = {
                    EstadoCita.PENDIENTE: {
                        EstadoCita.CONFIRMADA,
                        EstadoCita.CANCELADA,
                    },
                    EstadoCita.CONFIRMADA: {
                        EstadoCita.CANCELADA,
                        EstadoCita.COMPLETADA,
                    },
                    EstadoCita.CANCELADA: set(),
                    EstadoCita.COMPLETADA: set(),
                }

            if (
                estado_nuevo != estado_actual
                and estado_nuevo not in transiciones_permitidas[estado_actual]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"No se permite cambiar el estado de "
                        f"'{estado_actual.value}' a '{estado_nuevo.value}'"
                    ),
                )

            if "fecha_hora" in actualizacion and actualizacion["fecha_hora"] is not None:
                try:
                    fecha_hora = datetime.fromisoformat(actualizacion["fecha_hora"])
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La fecha y hora deben tener formato ISO 8601"
                    ) from exc

                ahora = datetime.now(fecha_hora.tzinfo)
                if fecha_hora <= ahora:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se puede agendar una cita en el pasado"
                    )

            datos.update(actualizacion)

            cita_modificada = Cita(**datos)
            db_citas[idx] = cita_modificada
            return cita_modificada

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )


@router.delete("/{cita_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cita(cita_id: int):
    for idx, cita in enumerate(db_citas):
        if cita.id == cita_id:
            db_citas.pop(idx)
            return None

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"No existe una cita con el ID {cita_id}",
                "details": []
            }
        }
    )
