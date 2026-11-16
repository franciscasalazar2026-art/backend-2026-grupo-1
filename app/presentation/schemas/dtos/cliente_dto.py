import re
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar_email_flexible(value: str) -> str:
    limpio = value.strip().lower()
    if not _EMAIL_REGEX.match(limpio):
        raise ValueError("El correo electrónico debe tener un formato válido (ej. usuario@dominio.cl).")
    return limpio


EmailFlexible = Annotated[str, AfterValidator(_validar_email_flexible)]


class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del cliente")
    email: EmailFlexible = Field(..., description="Correo electrónico del cliente (acepta dominios de prueba .test)")
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
