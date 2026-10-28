import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.models import ProfesionalServicioORM


def test_duplicate_professional_service_assignment_is_rejected(
    db_session, agenda_ids
):
    db_session.add(
        ProfesionalServicioORM(
            profesional_id=agenda_ids["profesional_id"],
            servicio_id=agenda_ids["servicio_id"],
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.skip(reason="El router /profesionales aún no está integrado en main")
def test_profesionales_crud_and_service_assignments(client):
    created = client.post(
        "/profesionales",
        json={
            "nombre": "Profesional Nueva",
            "especialidad": "Manicure",
            "email": "profesional.nueva@example.test",
            "telefono": "912345678",
            "activo": True,
        },
    )
    assert created.status_code == 201
    profesional_id = created.json()["id"]
    assert client.get(f"/profesionales/{profesional_id}").status_code == 200

    servicio = client.post(
        "/servicios",
        json={
            "nombre": "Manicure de prueba",
            "duracion_minutos": 30,
            "precio": "10000",
            "activo": True,
        },
    )
    assignment = client.post(
        f"/profesionales/{profesional_id}/servicios",
        json={"servicio_id": servicio.json()["id"]},
    )
    assert assignment.status_code == 201
    assert client.post(
        f"/profesionales/{profesional_id}/servicios",
        json={"servicio_id": servicio.json()["id"]},
    ).status_code == 409
