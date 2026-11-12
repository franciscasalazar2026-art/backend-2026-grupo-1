
from decimal import Decimal
from typing import Optional
from datetime import date, time

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.domain.models import EstadoCita


class ServicioCitaCreate(BaseModel):
    servicio_id: int = Field(..., gt=0)
    profesional_id: int = Field(..., gt=0)


class CitaCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    servicios: list[ServicioCitaCreate] = Field(default_factory=list)

    # Compatibilidad con solicitudes antiguas de un solo servicio.
    servicio_id: Optional[int] = Field(None, gt=0)
    profesional_id: Optional[int] = Field(None, gt=0)

    fecha: date
    hora: time
    motivo: str = Field(..., min_length=3, max_length=200)

    @model_validator(mode="after")
    def asegurar_servicios(self):
        if not self.servicios:
            if self.servicio_id is None or self.profesional_id is None:
                raise ValueError(
                    "Debes indicar al menos un servicio y su profesional."
                )

            self.servicios = [
                ServicioCitaCreate(
                    servicio_id=self.servicio_id,
                    profesional_id=self.profesional_id,
                )
            ]

        return self


class CitaUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[time] = None
    motivo: Optional[str] = Field(None, min_length=3, max_length=200)
    estado: Optional[EstadoCita] = None


class DetalleCitaResponse(BaseModel):
    servicio_id: int
    servicio_nombre: str
    profesional_id: int
    profesional_nombre: str
    fecha_inicio: date
    hora_inicio: time
    duracion_minutos: int
    precio: Decimal


class Cita(BaseModel):
    id: int
    cliente_id: int
    fecha: date
    hora: time
    motivo: str
    estado: EstadoCita

    servicio_id: Optional[int] = None
    profesional_id: Optional[int] = None

    servicios: list[DetalleCitaResponse] = Field(default_factory=list)


    model_config = {"from_attributes": True}
