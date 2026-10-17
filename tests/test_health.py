from fastapi.testclient import TestClient

from main import app


def test_healthcheck() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
