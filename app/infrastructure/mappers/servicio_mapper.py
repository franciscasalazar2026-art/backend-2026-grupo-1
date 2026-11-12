
from app.domain.entities.servicio import Servicio
from app.infrastructure.models.servicio import ServicioORM


class ServicioMapper:

    @staticmethod
    def a_entidad(modelo: ServicioORM) -> Servicio:
        return Servicio(
            id=modelo.id,
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            duracion_minutos=modelo.duracion_minutos,
            precio=modelo.precio,
            activo=modelo.activo,
        )

    @staticmethod
    def a_modelo(entidad: Servicio) -> ServicioORM:
        datos = {
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
            "duracion_minutos": entidad.duracion_minutos,
            "precio": entidad.precio,
            "activo": entidad.activo,
        }

        if entidad.id is not None:
            datos["id"] = entidad.id

        return ServicioORM(**datos)
