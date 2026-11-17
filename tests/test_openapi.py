"""Regression checks for the API contract exposed to Swagger UI."""


def test_openapi_documents_routes_parameters_models_and_status_codes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    expected_operations = {
        ("/auth/registro", "post"): {"201", "409", "422"},
        ("/auth/login", "post"): {"200", "401", "422", "429"},
        ("/auth/me", "get"): {"200", "401"},
        ("/auth/refresh", "post"): {"200", "401", "422"},
        ("/auth/logout", "post"): {"200", "422"},
        ("/auth/forgot-password", "post"): {"200", "422"},
        ("/auth/reset-password", "post"): {"200", "400", "401", "404", "422"},
        ("/clientes", "get"): {"200", "401"},
        ("/clientes", "post"): {"201", "401", "403", "409", "422"},
        ("/clientes/{cliente_id}", "get"): {"200", "401", "404"},
        ("/clientes/{cliente_id}", "put"): {"200", "401", "403", "404", "409", "422"},
        ("/clientes/{cliente_id}", "delete"): {"204", "401", "403", "404", "409"},
        ("/servicios", "get"): {"200"},
        ("/servicios", "post"): {"201", "401", "403", "409", "422"},
        ("/servicios/{servicio_id}", "get"): {"200", "404"},
        ("/servicios/{servicio_id}", "put"): {"200", "401", "403", "404", "409", "422"},
        ("/servicios/{servicio_id}", "delete"): {"204", "401", "403", "404"},
        ("/servicios/{servicio_id}/restaurar", "patch"): {"200", "401", "403", "404"},
        ("/citas", "get"): {"200"},
        ("/citas", "post"): {"201", "409", "422"},
        ("/citas/{cita_id}", "get"): {"200", "404"},
        ("/citas/{cita_id}", "put"): {"200", "404", "409", "422"},
        ("/citas/{cita_id}", "delete"): {"204", "404", "409"},
    }

    missing_statuses = {
        (path, method): sorted(codes - set(paths[path][method]["responses"]))
        for (path, method), codes in expected_operations.items()
        if codes - set(paths[path][method]["responses"])
    }
    assert not missing_statuses, missing_statuses

    bearer_scheme = schema["components"]["securitySchemes"]["HTTPBearer"]
    assert (bearer_scheme["type"], bearer_scheme["scheme"]) == ("http", "bearer")
    bearer_operations = (
        ("/auth/me", "get"),
        ("/clientes", "get"),
        ("/clientes", "post"),
        ("/servicios", "post"),
    )
    for path, method in bearer_operations:
        assert {"HTTPBearer": []} in paths[path][method]["security"]

    for path in (
        "/clientes/{cliente_id}",
        "/servicios/{servicio_id}",
        "/citas/{cita_id}",
    ):
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
    assert (
        "ClienteCreate"
        in cliente_create["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )
    assert (
        "Cliente"
        in cliente_create["responses"]["201"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )
    cliente_update = paths["/clientes/{cliente_id}"]["put"]
    assert (
        "ClienteUpdate"
        in cliente_update["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )

    service_create = paths["/servicios"]["post"]
    assert (
        "ServicioCreate"
        in service_create["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )
    assert service_create["responses"]["201"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/Servicio")
    service_update = paths["/servicios/{servicio_id}"]["put"]
    assert (
        "ServicioUpdate"
        in service_update["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )

    cita_create = paths["/citas"]["post"]
    assert (
        "CitaCreate"
        in cita_create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    )
    assert (
        "Cita"
        in cita_create["responses"]["201"]["content"]["application/json"]["schema"][
            "$ref"
        ]
    )
    cita_update = paths["/citas/{cita_id}"]["put"]
    assert (
        "CitaUpdate"
        in cita_update["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    )

    service_list_parameters = {
        parameter["name"] for parameter in paths["/servicios"]["get"]["parameters"]
    }
    assert {
        "buscar",
        "solo_activos",
        "ordenar_por",
        "direccion",
        "pagina",
        "limite",
    } <= service_list_parameters
