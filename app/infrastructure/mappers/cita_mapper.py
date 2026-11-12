
from app.domain.entities.cita import Cita
from app.domain.entities.detalle_cita import DetalleCita


class CitaMapper:

    @staticmethod
    def a_entidad(datos: dict) -> Cita:
        servicios = [
            DetalleCita(
                servicio_id=item["servicio_id"],
                servicio_nombre=item["servicio_nombre"],
                profesional_id=item["profesional_id"],
                profesional_nombre=item["profesional_nombre"],
                fecha_hora_inicio=item["fecha_hora_inicio"],
                duracion_minutos=item["duracion_minutos"],
                precio=item["precio"],
            )
            for item in datos["servicios"]
        ]

        return Cita(
            id=datos["id"],
            cliente_id=datos["cliente_id"],
            fecha_hora=datos["fecha_hora"],
            motivo=datos["motivo"],
            estado=datos["estado"],
            servicios=servicios,
        )
