from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.presentation.schemas.dtos.cliente_dto import EmailFlexible


class ProfesionalBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del profesional")
    especialidad: str = Field(..., min_length=2, max_length=100, description="Especialidad principal")
    email: EmailFlexible = Field(..., description="Correo electrónico del profesional")
    telefono: str = Field(..., min_length=8, max_length=15, description="Teléfono de contacto")


class ProfesionalCreate(ProfesionalBase):
    activo: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Valeria Muñoz",
                "especialidad": "Estilista",
                "email": "valeria.munoz@ejemplo.test",
                "telefono": "+56911223344",
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "especialidad": "Colorimetría",
                "telefono": "+56999887766",
            }
        }
    )


class Profesional(ProfesionalBase):
    id: int
    activo: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nombre": "Valeria Muñoz",
                "especialidad": "Estilista",
                "email": "valeria.munoz@ejemplo.test",
                "telefono": "+56911223344",
                "activo": True,
            }
        },
    )
