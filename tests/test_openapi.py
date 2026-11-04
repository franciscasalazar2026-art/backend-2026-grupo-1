"""Regression checks for the API contract exposed to Swagger UI."""


def test_openapi_documents_routes_parameters_models_and_status_codes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    expected_operations = {
        ("/clientes", "get"): {"200"},
        ("/clientes", "post"): {"201", "409", "422"},
        ("/clientes/{cliente_id}", "get"): {"200", "404"},
        ("/clientes/{cliente_id}", "put"): {"200", "404", "409", "422"},
        ("/clientes/{cliente_id}", "delete"): {"204", "404", "409"},
        ("/servicios", "get"): {"200"},
        ("/servicios", "post"): {"201", "409", "422"},
        ("/servicios/{servicio_id}", "get"): {"200", "404"},
        ("/servicios/{servicio_id}", "put"): {"200", "404", "409", "422"},
        ("/servicios/{servicio_id}", "delete"): {"204", "404"},
        ("/servicios/{servicio_id}/restaurar", "patch"): {"200", "404"},
        ("/citas", "get"): {"200"},
        ("/citas", "post"): {"201", "400", "409", "422"},
        ("/citas/{cita_id}", "get"): {"200", "404"},
        ("/citas/{cita_id}", "put"): {"200", "400", "404", "409", "422"},
        ("/citas/{cita_id}", "delete"): {"204", "404", "409"},
    }

    for (path, method), documented_codes in expected_operations.items():
        operation = paths[path][method]
        assert documented_codes <= set(operation["responses"]), (path, method)

    for path in ("/clientes/{cliente_id}", "/servicios/{servicio_id}", "/citas/{cita_id}"):
        get_operation = paths[path]["get"]
        assert any(
            parameter["in"] == "path" and parameter["required"]
            for parameter in get_operation["parameters"]
        )

    client_list_parameters = {
        parameter["name"] for parameter in paths["/clientes"]["get"]["parameters"]
    }
    assert {"limit", "offset"} <= client_list_parameters

    cliente_create = paths["/clientes"]["post"]
    assert "ClienteCreate" in cliente_create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert "Cliente" in cliente_create["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    cliente_update = paths["/clientes/{cliente_id}"]["put"]
    assert "ClienteUpdate" in cliente_update["requestBody"]["content"]["application/json"]["schema"]["$ref"]

    service_create = paths["/servicios"]["post"]
    assert "ServicioCreate" in service_create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert "ServicioResponse" in service_create["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    service_update = paths["/servicios/{servicio_id}"]["put"]
    assert "ServicioUpdate" in service_update["requestBody"]["content"]["application/json"]["schema"]["$ref"]

    cita_create = paths["/citas"]["post"]
    assert "CitaCreate" in cita_create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert "Cita" in cita_create["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    cita_update = paths["/citas/{cita_id}"]["put"]
    assert "CitaUpdate" in cita_update["requestBody"]["content"]["application/json"]["schema"]["$ref"]

    service_list_parameters = {
        parameter["name"] for parameter in paths["/servicios"]["get"]["parameters"]
    }
    assert {"buscar", "solo_activos", "ordenar_por", "direccion", "pagina", "limite"} <= service_list_parameters

