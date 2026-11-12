
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

from app.infrastructure.repositories.profesional_repository import (
    ProfesionalRepository,
)
from app.infrastructure.repositories.cliente_repository import (
    ClienteRepository,
)

from app.application.services.profesional_servicio import (
    ServicioProfesional,
)
from app.application.services.cliente_servicio import (
    ClienteServicio,
)

from app.infrastructure.repositories.servicio_repository import (
    ServicioRepository,
)

from app.application.services.servicio_servicio import (
    ServicioAplicacion,
)

from app.infrastructure.repositories.cita_repository import (
    CitaRepository,
)

from app.application.services.cita_servicio import (
    CitaServicio,
)


def obtener_servicio_profesional(
    db: Session = Depends(get_db),
) -> ServicioProfesional:
    repositorio = ProfesionalRepository(db)
    return ServicioProfesional(repositorio)


def obtener_servicio_cliente(
    db: Session = Depends(get_db),
) -> ClienteServicio:
    repositorio = ClienteRepository(db)
    return ClienteServicio(repositorio)

def obtener_servicio_aplicacion(
    db: Session = Depends(get_db),
) -> ServicioAplicacion:

    repositorio = ServicioRepository(db)

    return ServicioAplicacion(repositorio)

def obtener_servicio_cita(
    db: Session = Depends(get_db),
) -> CitaServicio:

    repositorio = CitaRepository(db)

    return CitaServicio(repositorio)