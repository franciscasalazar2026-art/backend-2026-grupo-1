def cliente_payload(**overrides):
    payload = {
        "nombre": "Isidora Valverde",
        "email": "isidora@example.com",
        "telefono": "912345678",
    }
    payload.update(overrides)
    return payload


def test_create_and_get_cliente(client):
    created = client.post("/clientes", json=cliente_payload())

    assert created.status_code == 201
    cliente_id = created.json()["id"]
    fetched = client.get(f"/clientes/{cliente_id}")

    assert fetched.status_code == 200
    assert fetched.json()["email"] == "isidora@example.com"


def test_duplicate_cliente_email_returns_conflict(client):
    assert client.post("/clientes", json=cliente_payload()).status_code == 201

    duplicate = client.post(
        "/clientes",
        json=cliente_payload(nombre="Otra Cliente"),
    )

    assert duplicate.status_code == 409


def test_invalid_cliente_email_returns_validation_error(client):
    response = client.post(
        "/clientes",
        json=cliente_payload(email="correo-invalido"),
    )

    assert response.status_code == 422


def test_missing_cliente_returns_not_found(client):
    response = client.get("/clientes/999999")

    assert response.status_code == 404


def test_list_clientes_reports_filtered_page_metadata(client):
    for number in range(3):
        result = client.post(
            "/clientes",
            json=cliente_payload(
                nombre=f"Cliente {number}", email=f"cliente{number}@example.com"
            ),
        )
        assert result.status_code == 201

    response = client.get("/clientes?limit=2&offset=1")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2
    assert response.json()["pagina"] == 1
