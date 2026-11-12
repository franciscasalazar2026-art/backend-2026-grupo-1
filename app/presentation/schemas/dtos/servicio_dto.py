
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ServicioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: str | None = Field(None, max_length=255)
    duracion_minutos: int = Field(..., gt=0)
    precio: Decimal = Field(..., ge=0)


class ServicioCreate(ServicioBase):
    activo: bool = True


class ServicioUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=100)
    descripcion: str | None = Field(None, max_length=255)
    duracion_minutos: int | None = Field(None, gt=0)
    precio: Decimal | None = Field(None, ge=0)
    activo: bool | None = None


class Servicio(ServicioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activo: bool
