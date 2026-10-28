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


def test_create_and_list_servicios(client):
    created = client.post("/servicios", json=servicio_payload())

    assert created.status_code == 201
    listed = client.get("/servicios")

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]


@pytest.mark.parametrize(
    "changes",
    [
        {"precio": "-1.00"},
        {"duracion_minutos": 0},
    ],
)
def test_invalid_service_values_return_422(client, changes):
    response = client.post("/servicios", json=servicio_payload(**changes))

    assert response.status_code == 422


@pytest.mark.skip(reason="GET /servicios/{servicio_id} aún no está integrado en main")
def test_get_missing_servicio_returns_not_found(client):
    assert client.get("/servicios/999999").status_code == 404


@pytest.mark.skip(reason="PUT /servicios/{servicio_id} aún no está integrado en main")
def test_update_servicio_and_validate_missing_id(client):
    created = client.post("/servicios", json=servicio_payload())
    servicio_id = created.json()["id"]
    updated = client.put(
        f"/servicios/{servicio_id}",
        json={"precio": "15000.00"},
    )

    assert updated.status_code == 200
    assert updated.json()["precio"] == "15000.00"
    assert client.put("/servicios/999999", json={"precio": "15000"}).status_code == 404


@pytest.mark.skip(reason="DELETE /servicios/{servicio_id} aún no está integrado en main")
def test_delete_servicio_and_validate_missing_id(client):
    created = client.post("/servicios", json=servicio_payload())
    servicio_id = created.json()["id"]

    assert client.delete(f"/servicios/{servicio_id}").status_code == 204
    assert client.delete("/servicios/999999").status_code == 404
