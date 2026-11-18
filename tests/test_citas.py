from datetime import datetime, time, timedelta

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    DetalleReservaORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)


def horario_futuro(dias=3):
    return datetime.combine(datetime.now().date() + timedelta(days=dias), time(10))


def cita_payload(agenda_ids, *, inicio=None, **overrides):
    inicio = inicio or horario_futuro()
    payload = {
        "cliente_id": agenda_ids["cliente_id"],
        "servicio_id": agenda_ids["servicio_id"],
        "profesional_id": agenda_ids["profesional_id"],
        "fecha": inicio.date().isoformat(),
        "hora": inicio.time().isoformat(),
        "motivo": "Prueba de agenda",
    }
    payload.update(overrides)
    return payload


def test_create_cita_creates_reserva_and_cita(client, agenda_ids, db_session):
    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 201
    assert response.json()["cliente_id"] == agenda_ids["cliente_id"]
    assert db_session.scalar(select(func.count(ReservaORM.id))) == 1
    assert db_session.scalar(select(func.count(CitaORM.id))) == 1


def test_cita_schedules_multiple_services_in_order(client, agenda_ids, db_session):
    second_service = ServicioORM(
        nombre="Pedicure de prueba",
        duracion_minutos=30,
        precio="8000.00",
        activo=True,
    )
    db_session.add(second_service)
    db_session.flush()
    db_session.add(
        ProfesionalServicioORM(
            profesional_id=agenda_ids["profesional_id"], servicio_id=second_service.id
        )
    )
    db_session.commit()
    start = horario_futuro()
    payload = {
        "cliente_id": agenda_ids["cliente_id"],
        "fecha": start.date().isoformat(),
        "hora": start.time().isoformat(),
        "motivo": "Reserva con dos servicios",
        "servicios": [
            {
                "servicio_id": service_id,
                "profesional_id": agenda_ids["profesional_id"],
            }
            for service_id in (agenda_ids["servicio_id"], second_service.id)
        ],
    }

    created = client.post("/citas", json=payload)

    assert created.status_code == 201, created.text
    response = created.json()
    details = response["servicios"]
    assert response["servicio_id"] is None
    assert [detail["servicio_id"] for detail in details] == [
        agenda_ids["servicio_id"],
        second_service.id,
    ]
    assert [detail["hora_inicio"] for detail in details] == ["10:00:00", "10:45:00"]
    assert db_session.scalar(select(func.count(DetalleReservaORM.id))) == 2

    updated = client.put(f"/citas/{response['id']}", json={"hora": "12:00:00"})
    assert updated.status_code == 200, updated.text
    assert [detail["hora_inicio"] for detail in updated.json()["servicios"]] == [
        "12:00:00",
        "12:45:00",
    ]


def test_reschedule_conflict_keeps_original_appointment_time(client, agenda_ids):
    start = horario_futuro()
    original = client.post("/citas", json=cita_payload(agenda_ids, inicio=start))
    another = client.post(
        "/citas", json=cita_payload(agenda_ids, inicio=start + timedelta(hours=1))
    )
    assert original.status_code == another.status_code == 201
    path = f"/citas/{another.json()['id']}"

    rescheduled = client.put(path, json={"hora": "10:15:00"})

    assert rescheduled.status_code == 409, rescheduled.text
    assert client.get(path).json()["hora"] == "11:00:00"


def test_cancelled_appointment_releases_its_time_slot(client, agenda_ids):
    payload = cita_payload(agenda_ids)
    created = client.post("/citas", json=payload)
    assert created.status_code == 201, created.text
    cancelled = client.put(
        f"/citas/{created.json()['id']}", json={"estado": "cancelada"}
    )
    assert cancelled.status_code == 200, cancelled.text

    new_booking = client.post("/citas", json=payload)

    assert new_booking.status_code == 201, new_booking.text
    assert new_booking.json()["id"] != created.json()["id"]


def test_invalid_cita_date_returns_422(client, agenda_ids):
    response = client.post(
        "/citas",
        json=cita_payload(agenda_ids, fecha="not-a-date"),
    )

    assert response.status_code == 422


def test_missing_cita_returns_404(client):
    assert client.get("/citas/999999").status_code == 404


def test_list_citas_filters_orders_and_paginates(client, agenda_ids):
    for day in (2, 5):
        response = client.post(
            "/citas",
            json=cita_payload(
                agenda_ids,
                inicio=horario_futuro(day),
            ),
        )
        assert response.status_code == 201

    response = client.get(
        "/citas?estado=pendiente&ordenar_por=fecha_hora&direccion=desc&pagina=1&limite=1"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    assert response.json()["pagina"] == 1
    assert response.json()["items"][0]["fecha"] == horario_futuro(5).date().isoformat()


def test_past_cita_is_rejected(client, agenda_ids):
    past = horario_futuro(-1)

    assert (
        client.post("/citas", json=cita_payload(agenda_ids, inicio=past)).status_code
        == 422
    )


def test_failure_after_reservation_flush_rolls_back_both_records(
    client, agenda_ids, db_session
):
    def fail_on_cita_flush(
        session: Session, _flush_context: object, _instances: object
    ) -> None:
        if any(isinstance(item, CitaORM) for item in session.new):
            raise IntegrityError("simulated cita failure", {}, RuntimeError())

    event.listen(Session, "before_flush", fail_on_cita_flush)
    try:
        response = client.post("/citas", json=cita_payload(agenda_ids))
    finally:
        event.remove(Session, "before_flush", fail_on_cita_flush)

    assert response.status_code == 409
    assert db_session.scalar(select(func.count(ReservaORM.id))) == 0
    assert db_session.scalar(select(func.count(CitaORM.id))) == 0


def test_overlapping_cita_for_same_professional_returns_conflict(client, agenda_ids):
    start = horario_futuro()
    first = client.post("/citas", json=cita_payload(agenda_ids, inicio=start))
    second = client.post("/citas", json=cita_payload(agenda_ids, inicio=start))

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.parametrize(
    ("estado_nuevo", "codigo_esperado"),
    [
        ("confirmada", 200),
        ("cancelada", 200),
    ],
)
def test_transiciones_permitidas_desde_pendiente(
    client, agenda_ids, estado_nuevo, codigo_esperado
):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    response = client.put(
        f"/citas/{cita_id}",
        json={"estado": estado_nuevo},
    )

    assert response.status_code == codigo_esperado
    assert response.json()["estado"] == estado_nuevo


def test_transicion_confirmada_a_completada(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    confirmacion = client.put(
        f"/citas/{cita_id}",
        json={"estado": "confirmada"},
    )
    assert confirmacion.status_code == 200

    completada = client.put(
        f"/citas/{cita_id}",
        json={"estado": "completada"},
    )

    assert completada.status_code == 200
    assert completada.json()["estado"] == "completada"


@pytest.mark.parametrize(
    ("estados_previos", "estado_nuevo"),
    [
        (["cancelada"], "confirmada"),
        (["confirmada", "completada"], "pendiente"),
    ],
)
def test_transiciones_no_permitidas(client, agenda_ids, estados_previos, estado_nuevo):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    for estado in estados_previos:
        cambio = client.put(
            f"/citas/{cita_id}",
            json={"estado": estado},
        )
        assert cambio.status_code == 200, cambio.text

    response = client.put(
        f"/citas/{cita_id}",
        json={"estado": estado_nuevo},
    )

    assert response.status_code == 422, response.text


def test_actualizar_cita_a_fecha_pasada_es_rechazado(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    pasada = horario_futuro(-1).date().isoformat()

    response = client.put(
        f"/citas/{cita_id}",
        json={"fecha": pasada},
    )

    assert response.status_code == 422


def test_obtener_cita_existente(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    response = client.get(f"/citas/{cita_id}")

    assert response.status_code == 200
    assert response.json()["id"] == cita_id


def test_actualizar_motivo_cita(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    response = client.put(
        f"/citas/{cita_id}",
        json={"motivo": "Consulta de seguimiento"},
    )

    assert response.status_code == 200
    assert response.json()["motivo"] == "Consulta de seguimiento"


def test_eliminar_cita(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    response = client.delete(f"/citas/{cita_id}")

    assert response.status_code == 204

    consulta = client.get(f"/citas/{cita_id}")
    assert consulta.status_code == 404


def test_eliminar_cita_inexistente(client):
    response = client.delete("/citas/999999")

    assert response.status_code == 404


def test_servicio_inexistente_retorna_error(client, agenda_ids):
    payload = cita_payload(agenda_ids)
    payload["servicio_id"] = 999999

    response = client.post("/citas", json=payload)

    assert response.status_code == 422


def test_profesional_inexistente_retorna_error(client, agenda_ids):
    payload = cita_payload(agenda_ids)
    payload["profesional_id"] = 999999

    response = client.post("/citas", json=payload)

    assert response.status_code == 422


def test_profesional_sin_asignacion_al_servicio_retorna_error(
    client, agenda_ids, db_session
):
    otro_profesional = ProfesionalORM(
        nombre="Profesional sin asignación",
        especialidad="Estética",
        email="sin.asignacion@example.test",
        telefono="911111111",
        activo=True,
    )

    db_session.add(otro_profesional)
    db_session.commit()

    payload = cita_payload(agenda_ids)
    payload["profesional_id"] = otro_profesional.id

    response = client.post("/citas", json=payload)

    assert response.status_code == 422


def test_cliente_inactivo_no_puede_crear_cita(client, agenda_ids, db_session):
    cliente = db_session.get(ClienteORM, agenda_ids["cliente_id"])
    cliente.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 422


def test_servicio_inactivo_no_puede_crear_cita(client, agenda_ids, db_session):
    servicio = db_session.get(ServicioORM, agenda_ids["servicio_id"])
    servicio.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 422


def test_profesional_inactivo_no_puede_crear_cita(client, agenda_ids, db_session):
    profesional = db_session.get(ProfesionalORM, agenda_ids["profesional_id"])
    profesional.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 422


def test_solapamiento_parcial_de_citas_retorna_conflicto(client, agenda_ids):
    inicio = horario_futuro()

    primera = client.post(
        "/citas",
        json=cita_payload(agenda_ids, inicio=inicio),
    )
    assert primera.status_code == 201

    # La segunda comienza 15 minutos después.
    # Como el servicio dura 45 minutos, ambas citas se superponen.
    segunda = client.post(
        "/citas",
        json=cita_payload(
            agenda_ids,
            inicio=inicio + timedelta(minutes=15),
        ),
    )

    assert segunda.status_code == 409


def test_cliente_inexistente_no_puede_crear_cita(client, agenda_ids):
    payload = cita_payload(agenda_ids)
    payload["cliente_id"] = 999999

    response = client.post("/citas", json=payload)

    assert response.status_code == 422
