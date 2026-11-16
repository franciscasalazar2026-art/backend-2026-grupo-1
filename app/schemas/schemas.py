import re
from decimal import Decimal
from typing import Annotated, Generic, List, Optional, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.domain.models import EstadoCita

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar_email_flexible(value: str) -> str:
    limpio = value.strip().lower()
    if not _EMAIL_REGEX.match(limpio):
        raise ValueError("El correo electrónico debe tener un formato válido (ej. usuario@dominio.cl).")
    return limpio


EmailFlexible = Annotated[str, AfterValidator(_validar_email_flexible)]


# --- CLIENTES ---
class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del cliente")
    email: EmailFlexible = Field(..., description="Correo electrónico del cliente (acepta dominios .test)")
    telefono: str = Field(..., min_length=8, max_length=15, description="Teléfono de contacto")


class ClienteCreate(ClienteBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Camila Soto",
                "email": "camila.soto@ejemplo.test",
                "telefono": "+56912345678",
            }
        }
    )


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailFlexible] = None
    telefono: Optional[str] = Field(None, min_length=8, max_length=15)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "telefono": "+56987654321",
            }
        }
    )


class Cliente(ClienteBase):
    id: int
    activo: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nombre": "Camila Soto",
                "email": "camila.soto@ejemplo.test",
                "telefono": "+56912345678",
                "activo": True,
            }
        },
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cliente_id": 1,
                "servicios": [{"servicio_id": 1, "profesional_id": 1}],
                "fecha_hora": "2026-12-01T10:30:00",
                "motivo": "Corte y peinado",
            }
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estado": "confirmada",
                "motivo": "Confirmada por teléfono",
            }
        }
    )


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

    model_config = ConfigDict(from_attributes=True)


# --- PAGINACIÓN ---
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int


# --- SERVICIOS ---
class ServicioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del servicio (ej. Manicure, Peluquería)")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción breve del servicio")
    duracion_minutos: int = Field(..., gt=0, description="La duración debe ser mayor a 0 minutos")
    precio: Decimal = Field(..., ge=0, description="El precio no puede ser negativo")


class ServicioCreate(ServicioBase):
    activo: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Corte y Peinado",
                "descripcion": "Lavado, corte estilizado y secado",
                "duracion_minutos": 45,
                "precio": "15000.00",
                "activo": True,
            }
        }
    )


class ServicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    duracion_minutos: Optional[int] = Field(None, gt=0)
    precio: Optional[Decimal] = Field(None, ge=0)
    activo: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "precio": "18000.00",
                "duracion_minutos": 50,
            }
        }
    )


class ServicioResponse(ServicioBase):
    id: int
    activo: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nombre": "Corte y Peinado",
                "descripcion": "Lavado, corte estilizado y secado",
                "duracion_minutos": 45,
                "precio": "15000.00",
                "activo": True,
            }
        },
    )


# --- PROFESIONALES ---
class ProfesionalBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    especialidad: str = Field(..., min_length=2, max_length=100)
    email: EmailFlexible
    telefono: str = Field(..., min_length=8, max_length=15)


class ProfesionalCreate(ProfesionalBase):
    activo: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Valentina Ruiz",
                "especialidad": "Estilista Senior",
                "email": "valentina.ruiz@ejemplo.test",
                "telefono": "+56955554444",
                "activo": True,
            }
        }
    )


class ProfesionalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    especialidad: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailFlexible] = None
    telefono: Optional[str] = Field(None, min_length=8, max_length=15)
    activo: Optional[bool] = None


class Profesional(ProfesionalBase):
    id: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)