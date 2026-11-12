
from app.domain.entities.profesional import Profesional
from app.infrastructure.models.profesional import ProfesionalORM


class ProfesionalMapper:

    @staticmethod
    def a_entidad(modelo: ProfesionalORM) -> Profesional:
        return Profesional(
            id=modelo.id,
            nombre=modelo.nombre,
            especialidad=modelo.especialidad,
            email=modelo.email,
            telefono=modelo.telefono,
            activo=modelo.activo,
        )

    @staticmethod
    def a_modelo(entidad: Profesional) -> ProfesionalORM:
        datos = {
            "nombre": entidad.nombre,
            "especialidad": entidad.especialidad,
            "email": entidad.email,
            "telefono": entidad.telefono,
            "activo": entidad.activo,
        }

        if entidad.id is not None:
            datos["id"] = entidad.id

        return ProfesionalORM(**datos)
