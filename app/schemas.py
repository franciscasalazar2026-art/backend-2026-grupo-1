from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models import EstadoCita

# --- ESQUEMAS DE CLIENTE ---

class ClienteBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

class Cliente(ClienteBase):
    id: int

    class Config:
        from_attributes = True

# --- ESQUEMAS DE CITA ---

class CitaBase(BaseModel):
    cliente_id: int
    fecha_hora: datetime
    motivo: str
    estado: EstadoCita = EstadoCita.PENDIENTE
