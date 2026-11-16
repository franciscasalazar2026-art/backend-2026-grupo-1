from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServicioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del servicio (ej. Corte y Peinado)")
    descripcion: str | None = Field(None, max_length=255, description="Descripción breve del servicio")
    duracion_minutos: int = Field(..., gt=0, description="Duración estimada en minutos")
    precio: Decimal = Field(..., ge=0, description="Precio del servicio en pesos")


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
    nombre: str | None = Field(None, min_length=2, max_length=100)
    descripcion: str | None = Field(None, max_length=255)
    duracion_minutos: int | None = Field(None, gt=0)
    precio: Decimal | None = Field(None, ge=0)
    activo: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "precio": "18000.00",
                "duracion_minutos": 50,
            }
        }
    )


class Servicio(ServicioBase):
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
