import pytest
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