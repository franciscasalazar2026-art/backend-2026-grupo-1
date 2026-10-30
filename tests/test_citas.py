from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.models import CitaORM, ReservaORM

def cita_payload(agenda_ids, **overrides):
    payload = {
        "cliente_id": agenda_ids["cliente_id"],
        "servicio_id": agenda_ids["servicio_id"],
        "profesional_id": agenda_ids["profesional_id"],
        "fecha_hora": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
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

def test_invalid_cita_date_returns_422(client, agenda_ids):
    response = client.post(
        "/citas",
        json=cita_payload(agenda_ids, fecha_hora="not-a-date"),
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
                fecha_hora=(datetime.now(timezone.utc) + timedelta(days=day)).isoformat(),
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

def test_past_cita_is_rejected(client, agenda_ids):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    assert client.post(
        "/citas", json=cita_payload(agenda_ids, fecha_hora=past)
    ).status_code == 422

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

def test_overlapping_cita_for_same_professional_returns_conflict(
    client, agenda_ids
):
    start = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    first = client.post("/citas", json=cita_payload(agenda_ids, fecha_hora=start))
    second = client.post("/citas", json=cita_payload(agenda_ids, fecha_hora=start))

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
def test_transiciones_no_permitidas(
    client, agenda_ids, estados_previos, estado_nuevo
):
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

    assert response.status_code == 400, response.text

def test_actualizar_cita_a_fecha_pasada_es_rechazado(client, agenda_ids):
    creada = client.post("/citas", json=cita_payload(agenda_ids))
    cita_id = creada.json()["id"]

    pasada = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()

    response = client.put(
        f"/citas/{cita_id}",
        json={"fecha_hora": pasada},
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

    assert response.status_code == 400

def test_profesional_inexistente_retorna_error(client, agenda_ids):
    payload = cita_payload(agenda_ids)
    payload["profesional_id"] = 999999

    response = client.post("/citas", json=payload)

    assert response.status_code == 400

def test_profesional_sin_asignacion_al_servicio_retorna_error(
    client, agenda_ids, db_session
):
    from app.infrastructure.models import ProfesionalORM

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

    assert response.status_code == 400

def test_cliente_inactivo_no_puede_crear_cita(client, agenda_ids, db_session):
    from app.infrastructure.models import ClienteORM

    cliente = db_session.get(ClienteORM, agenda_ids["cliente_id"])
    cliente.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 400

def test_servicio_inactivo_no_puede_crear_cita(client, agenda_ids, db_session):
    from app.infrastructure.models import ServicioORM

    servicio = db_session.get(ServicioORM, agenda_ids["servicio_id"])
    servicio.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 400

def test_profesional_inactivo_no_puede_crear_cita(
    client, agenda_ids, db_session
):
    from app.infrastructure.models import ProfesionalORM

    profesional = db_session.get(
        ProfesionalORM, agenda_ids["profesional_id"]
    )
    profesional.activo = False
    db_session.commit()

    response = client.post("/citas", json=cita_payload(agenda_ids))

    assert response.status_code == 400

def test_solapamiento_parcial_de_citas_retorna_conflicto(client, agenda_ids):
    inicio = datetime.now(timezone.utc) + timedelta(days=3)

    primera = client.post(
        "/citas",
        json=cita_payload(agenda_ids, fecha_hora=inicio.isoformat()),
    )
    assert primera.status_code == 201

    # La segunda comienza 15 minutos después.
    # Como el servicio dura 45 minutos, ambas citas se superponen.
    segunda = client.post(
        "/citas",
        json=cita_payload(
            agenda_ids,
            fecha_hora=(inicio + timedelta(minutes=15)).isoformat(),
        ),
    )

    assert segunda.status_code == 409