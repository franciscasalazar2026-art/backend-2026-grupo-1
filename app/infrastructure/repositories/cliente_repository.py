
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models import ClienteORM
from app.infrastructure.mappers.cliente_mapper import ClienteMapper

from app.application.puertos.cliente_repositorio import (
    ClienteRepositorio,
    ConflictoRepositorio,
)


class ClienteRepository(ClienteRepositorio):

    def __init__(self, db: Session):
        self.db = db

    def listar(self, limite=10, desplazamiento=0):
        consulta = self.db.query(ClienteORM)

        total = consulta.count()

        modelos = (
            consulta.order_by(ClienteORM.id)
            .offset(desplazamiento)
            .limit(limite)
            .all()
        )

        clientes = [
            ClienteMapper.a_entidad(modelo)
            for modelo in modelos
        ]

        return clientes, total

    def obtener(self, cliente_id: int):
        modelo = self.db.get(ClienteORM, cliente_id)

        if modelo is None:
            return None

        return ClienteMapper.a_entidad(modelo)

    def crear(self, datos: dict):
        modelo = ClienteORM(**datos)
        self.db.add(modelo)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ClienteMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def actualizar(self, cliente, cambios: dict):
        modelo = self.db.get(ClienteORM, cliente.id)

        if modelo is None:
            return None

        for campo, valor in cambios.items():
            setattr(modelo, campo, valor)

        try:
            self.db.commit()
            self.db.refresh(modelo)

            return ClienteMapper.a_entidad(modelo)

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error

    def eliminar(self, cliente):
        modelo = self.db.get(ClienteORM, cliente.id)

        if modelo is None:
            return

        self.db.delete(modelo)

        try:
            self.db.commit()

        except IntegrityError as error:
            self.db.rollback()
            raise ConflictoRepositorio() from error
