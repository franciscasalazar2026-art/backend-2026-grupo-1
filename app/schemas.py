from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models import EstadoCita

# --- ESQUEMAS DE CLIENTE ---

class ClienteBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str