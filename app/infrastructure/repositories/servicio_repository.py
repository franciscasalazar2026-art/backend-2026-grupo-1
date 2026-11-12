
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models import ServicioORM
from app.infrastructure.mappers.servicio_mapper import ServicioMapper

from app.application.puertos.profesional_repositorio import (
    ConflictoRepositorio,
)

from app.application.puertos.servicio_repositorio import (
    ServicioRepositorio,
)


class ServicioRepository(ServicioRepositorio):

    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        buscar=None,
        solo_activos=True,
        ordenar_por="precio",
        direccion="asc",
        pagina=1,
        limite=10,
    ):
        consulta = self.db.query(ServicioORM)

        if solo_activos:
            consulta = consulta.filter(
                ServicioORM.activo.is_(True)
            )

        if buscar:
            consulta = consulta.filter(
                ServicioORM.nombre.ilike(f"%{buscar}%")
            )

        total = consulta.count()

        campos_permitidos = {
            "nombre": ServicioORM.nombre,
            "precio": ServicioORM.precio,
            "id": ServicioORM.id,
        }

        campo = campos_permitidos.get(
            ordenar_por,
            ServicioORM.precio,
        )

        if direccion.lower() == "desc":
            consulta = consulta.order_by(campo.desc())
        else:
            consulta = consulta.order_by(campo.asc())

        modelos = (
            consulta
            .offset((pagina - 1) * limite)
            .limit(limite)
            .all()
        )

        servicios = [
            ServicioMapper.a_entidad(modelo)
            for modelo in modelos
        ]

        return servicios, total

    def obtener(self, servicio_id: int):
        modelo = self.db.get(ServicioORM, servicio_id)

        if modelo is None:
            return None

        return ServicioMapper.a_entidad(modelo)

    def crear(self, datos: dict):
        modelo = ServicioORM(**datos)
        self.db.add(modelo)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ServicioMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def actualizar(self, servicio, cambios: dict):
        modelo = self.db.get(ServicioORM, servicio.id)

        if modelo is None:
            return None

        for campo, valor in cambios.items():
            setattr(modelo, campo, valor)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ServicioMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def desactivar(self, servicio):
        modelo = self.db.get(ServicioORM, servicio.id)

        if modelo is None:
            return

        modelo.activo = False
        self.db.commit()

    def restaurar(self, servicio):
        modelo = self.db.get(ServicioORM, servicio.id)

        if modelo is None:
            return None

        modelo.activo = True
        self.db.commit()
        self.db.refresh(modelo)

        return ServicioMapper.a_entidad(modelo)
