import pytest


def servicio_payload(**overrides):
    payload = {
        "nombre": "Corte de cabello",
        "descripcion": "Corte y peinado",
        "duracion_minutos": 45,
        "precio": "12000.00",
        "activo": True,
    }
    payload.update(overrides)
    return payload


def test_create_and_list_servicios(admin_client):
    created = admin_client.post("/servicios", json=servicio_payload())

    assert created.status_code == 201

    listed = admin_client.get("/servicios")

    assert listed.status_code == 200
    # Adaptado a la respuesta paginada estructurada:
    data = listed.json()
    assert "items" in data
    assert [item["id"] for item in data["items"]] == [created.json()["id"]]
    assert data["total"] == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"precio": "-1.00"},
        {"duracion_minutos": 0},
        {"duracion_minutos": -15},
    ],
)
def test_invalid_service_values_return_422(admin_client, changes):
    response = admin_client.post("/servicios", json=servicio_payload(**changes))

    assert response.status_code == 422


def test_get_missing_servicio_returns_not_found(admin_client):
    response = admin_client.get("/servicios/999999")
    assert response.status_code == 404


def test_update_servicio_and_validate_missing_id(admin_client):
    created = admin_client.post("/servicios", json=servicio_payload())
    servicio_id = created.json()["id"]

    updated = admin_client.put(
        f"/servicios/{servicio_id}",
        json={"precio": "15000.00"},
    )

    assert updated.status_code == 200
    assert updated.json()["precio"] == "15000.00"
    assert (
        admin_client.put("/servicios/999999", json={"precio": "15000.00"}).status_code
        == 404
    )


def test_delete_servicio_and_validate_missing_id(admin_client):
    created = admin_client.post("/servicios", json=servicio_payload())
    servicio_id = created.json()["id"]

    assert admin_client.delete(f"/servicios/{servicio_id}").status_code == 204
    assert admin_client.delete("/servicios/999999").status_code == 404


def test_restaurar_servicio_returns_it_to_public_catalog(admin_client):
    created = admin_client.post("/servicios", json=servicio_payload())
    assert created.status_code == 201, created.text
    path = f"/servicios/{created.json()['id']}"
    assert admin_client.delete(path).status_code == 204
    assert admin_client.get("/servicios").json()["total"] == 0

    restored = admin_client.patch(f"{path}/restaurar")
    assert restored.status_code == 200, restored.text
    assert restored.json()["activo"] is True
    catalog = admin_client.get("/servicios").json()
    assert [item["id"] for item in catalog["items"]] == [created.json()["id"]]
    assert admin_client.patch("/servicios/999999/restaurar").status_code == 404
