from decimal import Decimal
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field
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
class CitaCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    servicio_id: int = Field(1, gt=0)
    profesional_id: int = Field(1, gt=0)
    fecha_hora: str
    motivo: str = Field(..., min_length=3, max_length=200)

class CitaUpdate(BaseModel):
    fecha_hora: Optional[str] = None
    motivo: Optional[str] = Field(None, min_length=3, max_length=200)
    estado: Optional[EstadoCita] = None

class Cita(BaseModel):
    id: int
    cliente_id: int
    servicio_id: int
    profesional_id: int
    fecha_hora: str
    motivo: str
    estado: EstadoCita

    class Config:
        from_attributes = True

# --- PAGINACIÃ“N ---
T = TypeVar('T')
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int

# --- SERVICIOS ---
class ServicioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del servicio (ej. Manicure, Peluquería)")
    descripcion: Optional[str] = Field(None, max_length=255)
    duracion_minutos: int = Field(..., gt=0, description="La duración debe ser mayor a 0 minutos")
    precio: Decimal = Field(..., ge=0, description="El precio no puede ser negativo")

class ServicioCreate(ServicioBase):
    activo: bool = True

class ServicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    duracion_minutos: Optional[int] = Field(None, gt=0)
    precio: Optional[Decimal] = Field(None, ge=0)
    activo: Optional[bool] = None

class ServicioResponse(ServicioBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True