from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.main.get_connection")
def test_health_ok(mock_get_connection):
    mock_conn = MagicMock()
    mock_get_connection.return_value.connect.return_value.__enter__.return_value = mock_conn

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"db": "ok"}


@patch("app.main.get_connection")
def test_health_unreachable(mock_get_connection):
    mock_get_connection.side_effect = Exception("connection refused")

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"db": "unreachable"}
