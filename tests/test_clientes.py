from app.infrastructure.models import ReservaORM


def cliente_payload(**overrides):
    payload = {
        "nombre": "Isidora Valverde",
        "email": "isidora@example.com",
        "telefono": "912345678",
    }
    payload.update(overrides)
    return payload


def test_create_and_get_cliente(admin_client):
    created = admin_client.post("/clientes", json=cliente_payload())

    assert created.status_code == 201
    cliente_id = created.json()["id"]
    fetched = admin_client.get(f"/clientes/{cliente_id}")

    assert fetched.status_code == 200
    assert fetched.json()["email"] == "isidora@example.com"


def test_duplicate_cliente_email_returns_conflict(admin_client):
    assert admin_client.post("/clientes", json=cliente_payload()).status_code == 201

    duplicate = admin_client.post(
        "/clientes",
        json=cliente_payload(nombre="Otra Cliente"),
    )

    assert duplicate.status_code == 409


def test_invalid_cliente_email_returns_validation_error(admin_client):
    response = admin_client.post(
        "/clientes",
        json=cliente_payload(email="correo-invalido"),
    )

    assert response.status_code == 422


def test_missing_cliente_returns_not_found(admin_client):
    response = admin_client.get("/clientes/999999")

    assert response.status_code == 404


def test_list_clientes_reports_filtered_page_metadata(admin_client):
    for number in range(3):
        result = admin_client.post(
            "/clientes",
            json=cliente_payload(
                nombre=f"Cliente {number}", email=f"cliente{number}@example.com"
            ),
        )
        assert result.status_code == 201

    response = admin_client.get("/clientes?limit=2&offset=1")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2
    assert response.json()["pagina"] == 1


def test_recepcionista_updates_and_deletes_cliente(client, auth_headers):
    headers = auth_headers("recepcionista")
    created = client.post("/clientes", json=cliente_payload(), headers=headers)
    assert created.status_code == 201, created.text
    path = f"/clientes/{created.json()['id']}"

    updated = client.put(path, json={"telefono": "987654321"}, headers=headers)
    assert updated.status_code == 200, updated.text
    assert updated.json()["telefono"] == "987654321"
    assert client.get(path, headers=headers).json()["telefono"] == "987654321"

    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404


def test_cliente_cannot_write_but_can_read_existing_cliente(client, auth_headers):
    payload = cliente_payload()
    admin = auth_headers("admin")
    created = client.post("/clientes", json=payload, headers=admin)
    assert created.status_code == 201, created.text
    path = f"/clientes/{created.json()['id']}"

    cliente = auth_headers("cliente")
    assert client.get(path).status_code == 401
    assert client.get(path, headers=cliente).status_code == 200
    denied = client.put(path, json={"telefono": "987654321"}, headers=cliente)
    assert denied.status_code == 403
    assert client.get(path, headers=admin).json()["telefono"] == payload["telefono"]


def test_update_cliente_duplicate_email_does_not_replace_old_value(admin_client):
    first = admin_client.post("/clientes", json=cliente_payload())
    second = admin_client.post(
        "/clientes", json=cliente_payload(email="distinto@example.com")
    )
    assert first.status_code == second.status_code == 201
    path = f"/clientes/{second.json()['id']}"

    updated = admin_client.put(path, json={"email": first.json()["email"]})

    assert updated.status_code == 409, updated.text
    assert admin_client.get(path).json()["email"] == second.json()["email"]


def test_cliente_with_existing_reservation_cannot_be_deleted(
    admin_client, agenda_ids, db_session
):
    cliente_id = agenda_ids["cliente_id"]
    db_session.add(ReservaORM(cliente_id=cliente_id))
    db_session.commit()
    path = f"/clientes/{cliente_id}"

    deleted = admin_client.delete(path)

    assert deleted.status_code == 409, deleted.text
    assert admin_client.get(path).status_code == 200
