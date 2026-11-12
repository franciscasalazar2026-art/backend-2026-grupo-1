
from app.domain.entities.cliente import Cliente
from app.infrastructure.models.cliente import ClienteORM


class ClienteMapper:

    @staticmethod
    def a_entidad(modelo: ClienteORM) -> Cliente:
        return Cliente(
            id=modelo.id,
            nombre=modelo.nombre,
            email=modelo.email,
            telefono=modelo.telefono,
            activo=modelo.activo,
        )

    @staticmethod
    def a_modelo(entidad: Cliente) -> ClienteORM:
        datos = {
            "nombre": entidad.nombre,
            "email": entidad.email,
            "telefono": entidad.telefono,
            "activo": entidad.activo,
        }

        if entidad.id is not None:
            datos["id"] = entidad.id

        return ClienteORM(**datos)
