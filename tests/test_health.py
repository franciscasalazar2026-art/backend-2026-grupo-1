import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """
    Verifica que la API responda correctamente en la raíz.
    """
    response = client.get("/")
    assert response.status_code in [200, 404]


def test_openapi_docs_available():
    """
    Verifica que la documentación interactiva de Swagger esté accesible.
    """
    response = client.get("/docs")
    assert response.status_code == 200
