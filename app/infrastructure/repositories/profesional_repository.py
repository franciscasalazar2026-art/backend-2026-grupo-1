
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models import (
    ProfesionalORM,
    ProfesionalServicioORM,
    ServicioORM,
)

from app.application.puertos.profesional_repositorio import (
    ProfesionalRepositorio,
    ConflictoRepositorio,
)

from app.infrastructure.mappers.profesional_mapper import ProfesionalMapper
from app.domain.entities.profesional import Profesional


class ProfesionalRepository(ProfesionalRepositorio):

    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        pagina=1,
        limite=10,
    ):
        consulta = self.db.query(ProfesionalORM)

        if solo_activos:
            consulta = consulta.filter(ProfesionalORM.activo.is_(True))

        if buscar:
            consulta = consulta.filter(
                ProfesionalORM.nombre.ilike(f"%{buscar}%")
            )

        total = consulta.count()

        modelos = (
            consulta.order_by(ProfesionalORM.id)
            .offset((pagina - 1) * limite)
            .limit(limite)
            .all()
        )

        profesionales = [
            ProfesionalMapper.a_entidad(modelo)
            for modelo in modelos
        ]

        return profesionales, total

    def obtener(self, profesional_id: int):
        modelo = self.db.get(ProfesionalORM, profesional_id)

        if modelo is None:
            return None

        return ProfesionalMapper.a_entidad(modelo)

    def obtener_servicio(self, servicio_id: int):
        return self.db.get(ServicioORM, servicio_id)

    def crear(self, datos: dict):
        modelo = ProfesionalORM(**datos)
        self.db.add(modelo)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ProfesionalMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def actualizar(self, profesional: Profesional, cambios: dict):
        modelo = self.db.get(ProfesionalORM, profesional.id)

        if modelo is None:
            return None

        for campo, valor in cambios.items():
            setattr(modelo, campo, valor)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ProfesionalMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def desactivar(self, profesional: Profesional):
        modelo = self.db.get(ProfesionalORM, profesional.id)

        if modelo is not None:
            modelo.activo = False
            self.db.commit()

    def restaurar(self, profesional: Profesional):
        modelo = self.db.get(ProfesionalORM, profesional.id)

        if modelo is None:
            return None

        modelo.activo = True
        self.db.commit()
        self.db.refresh(modelo)

        return ProfesionalMapper.a_entidad(modelo)

    def listar_servicios(self, profesional: Profesional):
        modelo = self.db.get(ProfesionalORM, profesional.id)

        if modelo is None:
            return []

        return [
            {
                "id": relacion.id,
                "servicio_id": relacion.servicio.id,
                "servicio_nombre": relacion.servicio.nombre,
            }
            for relacion in modelo.profesional_servicios
        ]

    def asignar_servicio(
        self,
        profesional_id: int,
        servicio_id: int,
    ):
        existente = (
            self.db.query(ProfesionalServicioORM)
            .filter_by(
                profesional_id=profesional_id,
                servicio_id=servicio_id,
            )
            .first()
        )

        if existente:
            return None

        asignacion = ProfesionalServicioORM(
            profesional_id=profesional_id,
            servicio_id=servicio_id,
        )

        self.db.add(asignacion)

        try:
            self.db.commit()
            self.db.refresh(asignacion)

            servicio = self.db.get(ServicioORM, servicio_id)

            return {
                "id": asignacion.id,
                "profesional_id": profesional_id,
                "servicio_id": servicio_id,
                "servicio_nombre": servicio.nombre,
            }

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error
