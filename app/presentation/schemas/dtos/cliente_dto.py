
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


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
