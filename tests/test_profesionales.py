import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models import ProfesionalServicioORM


def profesional_payload(**overrides):
    return {
        "nombre": "Profesional Nueva",
        "especialidad": "Manicure",
        "email": "profesional.nueva@example.com",
        "telefono": "912345678",
        "activo": True,
        **overrides,
    }


def test_duplicate_professional_service_assignment_is_rejected(db_session, agenda_ids):
    db_session.add(
        ProfesionalServicioORM(
            profesional_id=agenda_ids["profesional_id"],
            servicio_id=agenda_ids["servicio_id"],
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_profesionales_crud_and_service_assignments(admin_client):
    created = admin_client.post(
        "/profesionales",
        json=profesional_payload(),
    )
    assert created.status_code == 201
    profesional_id = created.json()["id"]
    assert admin_client.get(f"/profesionales/{profesional_id}").status_code == 200

    servicio = admin_client.post(
        "/servicios",
        json={
            "nombre": "Manicure de prueba",
            "duracion_minutos": 30,
            "precio": "10000",
            "activo": True,
        },
    )
    assert servicio.status_code == 201, servicio.text
    assignment = admin_client.post(
        f"/profesionales/{profesional_id}/servicios",
        json={"servicio_id": servicio.json()["id"]},
    )
    assert assignment.status_code == 201
    assert (
        admin_client.post(
            f"/profesionales/{profesional_id}/servicios",
            json={"servicio_id": servicio.json()["id"]},
        ).status_code
        == 409
    )

    catalog = admin_client.get(f"/profesionales/{profesional_id}/servicios")
    assert catalog.status_code == 200, catalog.text
    assert [item["servicio_id"] for item in catalog.json()] == [servicio.json()["id"]]

    path = f"/profesionales/{profesional_id}"
    updated = admin_client.put(path, json={"especialidad": "Pedicure"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["especialidad"] == "Pedicure"
    assert admin_client.delete(path).status_code == 204
    assert admin_client.get("/profesionales").json()["total"] == 0
    restored = admin_client.patch(f"{path}/restaurar")
    assert restored.status_code == 200, restored.text
    assert restored.json()["activo"] is True


def test_profesional_duplicate_email_is_rejected_on_create_and_update(admin_client):
    initial = profesional_payload()
    first = admin_client.post("/profesionales", json=initial)
    assert first.status_code == 201, first.text

    duplicate = admin_client.post("/profesionales", json=initial)
    assert duplicate.status_code == 409, duplicate.text

    other = profesional_payload(nombre="Profesional Distinta", email="otra@example.com")
    second = admin_client.post("/profesionales", json=other)
    assert second.status_code == 201, second.text
    path = f"/profesionales/{second.json()['id']}"
    duplicate_update = admin_client.put(path, json={"email": initial["email"]})
    assert duplicate_update.status_code == 409, duplicate_update.text
    assert admin_client.get(path).json()["email"] == other["email"]


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("GET", "", None),
        ("PUT", "", {"especialidad": "Masaje"}),
        ("DELETE", "", None),
        ("PATCH", "/restaurar", None),
        ("GET", "/servicios", None),
        ("POST", "/servicios", {"servicio_id": 1}),
    ],
)
def test_missing_professional_returns_not_found(client, method, suffix, body):
    response = client.request(method, f"/profesionales/98765{suffix}", json=body)

    assert response.status_code == 404, response.text


def test_rejects_assignment_for_invalid_service_or_inactive_professional(
    client, agenda_ids
):
    path = f"/profesionales/{agenda_ids['profesional_id']}"
    assignment_path = f"{path}/servicios"
    assert client.post(assignment_path, json={"servicio_id": True}).status_code == 422
    assert client.post(assignment_path, json={"servicio_id": 98765}).status_code == 404
    assert client.delete(path).status_code == 204
    assert (
        client.post(
            assignment_path,
            json={"servicio_id": agenda_ids["servicio_id"]},
        ).status_code
        == 404
    )
