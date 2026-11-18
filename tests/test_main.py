from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_and_health_report_the_same_api_version():
    health = client.get("/")
    contract = client.get("/openapi.json")

    assert health.status_code == contract.status_code == 200
    assert health.json()["version"] == contract.json()["info"]["version"]
