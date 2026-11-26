from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import create_app


def test_health_checks_database_and_disposes_engine():
    engine = MagicMock()
    with patch("app.main.build_engine", return_value=engine):
        with TestClient(create_app()) as client:
            response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    connection = engine.connect.return_value.__enter__.return_value
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"
    engine.dispose.assert_called_once()


def test_health_returns_503_without_exposing_credentials():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("secret_password", {}, Exception("db down"))
    with patch("app.main.build_engine", return_value=engine):
        with TestClient(create_app()) as client:
            response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_unavailable"
    assert "secret_password" not in response.text


def test_unknown_route_uses_error_envelope():
    with patch("app.main.build_engine"):
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_404"


def test_openapi_documents_health_and_unavailable_response():
    schema = create_app().openapi()
    assert schema["info"]["title"] == "PetCare API"
    assert {"200", "503"} <= schema["paths"]["/health"]["get"]["responses"].keys()
