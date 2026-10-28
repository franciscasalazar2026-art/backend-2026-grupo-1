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
=======
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.infrastructure.models  # Carga los modelos en SQLAlchemy
from app.main import app
from app.infrastructure.database import Base, get_db

# StaticPool mantiene la misma conexión SQLite en memoria abierta para todas las peticiones
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Crea la estructura de tablas antes de cada test y la limpia al finalizar."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_listar_servicios_exitoso():
    """Verifica que el endpoint GET /servicios retorne codigo 200 y una lista."""
    respuesta = client.get("/servicios")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_obtener_servicio_no_existente():
    """Verifica que al buscar un ID de servicio inexistente devuelva error 404."""
    respuesta = client.get("/servicios/999999")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Servicio con ID 999999 no encontrado."


def test_validacion_crear_servicio_duracion_invalida():
    """Verifica que no se permitan registrar servicios con duraciones no validas."""
    payload_invalido = {
        "nombre": "Corte Test Invalido",
        "descripcion": "Prueba de validacion DTO",
        "duracion_minutos": -15,
        "precio": 15000.0,
        "activo": True,
    }
    respuesta = client.post("/servicios", json=payload_invalido)
    assert respuesta.status_code == 422
