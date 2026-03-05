"""Tests for GET webhook verification and health check."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Validate health endpoint response.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Service is alive"}


def test_webhook_verification_success(client: TestClient):
    """Validate the Meta verification handshake for GET /webhook.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    # Datos simulando la petición de Meta
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_de_prueba_secreto",  # Coincide con conftest.py
        "hub.challenge": "123456789",
    }

    response = client.get("/webhook", params=params)

    assert response.status_code == 200
    # Meta espera recibir EXACTAMENTE el valor del challenge como texto plano/body
    assert response.text == "123456789"


def test_webhook_verification_invalid_token(client: TestClient):
    """Validate that invalid verify tokens return 403.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_hacker_incorrecto",
        "hub.challenge": "123456789",
    }

    response = client.get("/webhook", params=params)

    assert response.status_code == 403
    assert response.json()["detail"] == "Token inválido"


def test_webhook_verification_missing_params(client: TestClient):
    """Validate that missing query params return 400.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    # Falta verify_token y challenge
    params = {"hub.mode": "subscribe"}

    response = client.get("/webhook", params=params)

    assert response.status_code == 400
