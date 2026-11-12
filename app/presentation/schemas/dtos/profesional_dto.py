
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ProfesionalBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    especialidad: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=8, max_length=15)


class ProfesionalCreate(ProfesionalBase):
    activo: bool = True


class ProfesionalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    especialidad: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=8, max_length=15)
    activo: Optional[bool] = None


class Profesional(ProfesionalBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True
