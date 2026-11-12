
class CitaResponseMapper:

    @staticmethod
    def a_respuesta(cita):
        servicios = [
            {
                "servicio_id": item.servicio_id,
                "servicio_nombre": item.servicio_nombre,
                "profesional_id": item.profesional_id,
                "profesional_nombre": item.profesional_nombre,
                "fecha_inicio": item.fecha_hora_inicio.date(),
                "hora_inicio": item.fecha_hora_inicio.time(),
                "duracion_minutos": item.duracion_minutos,
                "precio": item.precio,
            }
            for item in cita.servicios
        ]

        return {
            "id": cita.id,
            "cliente_id": cita.cliente_id,
            "servicio_id": servicios[0]["servicio_id"] if len(servicios) == 1 else None,
            "profesional_id": servicios[0]["profesional_id"] if len(servicios) == 1 else None,
            "fecha": cita.fecha_hora.date(),
            "hora": cita.fecha_hora.time(),
            "motivo": cita.motivo,
            "estado": cita.estado,
            "servicios": servicios,
        }
