from decimal import Decimal
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.domain.models import EstadoCita

# --- CLIENTES ---
class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=8, max_length=15)

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=8, max_length=15)

class Cliente(ClienteBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True

# --- CITAS ---
class ServicioCitaCreate(BaseModel):
    servicio_id: int = Field(..., gt=0)
    profesional_id: int = Field(..., gt=0)


class CitaCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    servicios: List[ServicioCitaCreate] = Field(default_factory=list)

    # Compatibilidad con solicitudes antiguas de un solo servicio.
    servicio_id: Optional[int] = Field(None, gt=0)
    profesional_id: Optional[int] = Field(None, gt=0)

    fecha_hora: str
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
    fecha_hora: Optional[str] = None
    motivo: Optional[str] = Field(None, min_length=3, max_length=200)
    estado: Optional[EstadoCita] = None


class DetalleCitaResponse(BaseModel):
    servicio_id: int
    servicio_nombre: str
    profesional_id: int
    profesional_nombre: str
    fecha_hora_inicio: str
    duracion_minutos: int
    precio: Decimal


class Cita(BaseModel):
    id: int
    cliente_id: int
    fecha_hora: str
    motivo: str
    estado: EstadoCita

    # Se mantienen para respuestas de citas con un solo servicio.
    servicio_id: Optional[int] = None
    profesional_id: Optional[int] = None

    # Una cita puede contener varios servicios.
    servicios: List[DetalleCitaResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
# --- PAGINACIÃƒâ€œN ---
T = TypeVar('T')
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int


# --- SERVICIOS ---
class ServicioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    duracion_minutos: int = Field(..., gt=0)
    precio: Decimal = Field(..., ge=0)
    activo: bool = True


class ServicioResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    duracion_minutos: int
    precio: Decimal
    activo: bool

    class Config:
        from_attributes = True
