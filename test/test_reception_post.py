"""Tests for webhook POST reception and persistence."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.config.settings import settings

# Datos de prueba para un comentario
PAYLOAD_COMENTARIO = {
    "object": "instagram",
    "entry": [
        {
            "id": "17841405793187218",
            "time": 1699999999,
            "changes": [
                {
                    "field": "comments",
                    "value": {"id": "1791234567890", "text": "This is a test comment"},
                }
            ],
        }
    ],
}


def test_receive_webhook_success_no_signature(client: TestClient):
    """Validate POST flow when signature checks are disabled.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    # Aseguramos que la validación de firma esté apagada
    settings.VERIFY_SIGNATURE = False

    response = client.post("/webhook", json=PAYLOAD_COMENTARIO)

    assert response.status_code == 200
    assert response.json() == {"message": "Webhook recibido"}


@patch(
    "app.repositories.webhook_log_repository.WebhookLogRepository.save",
    new_callable=AsyncMock,
)
def test_webhook_processing_saves_to_db(mock_save, client: TestClient):
    """Validate that a valid webhook triggers repository persistence.

    Args:
        mock_save (AsyncMock): Mocked repository save method.
        client (TestClient): FastAPI test client fixture.
    """
    settings.VERIFY_SIGNATURE = False

    client.post("/webhook", json=PAYLOAD_COMENTARIO)

    # Verificamos que se haya intentado guardar
    assert mock_save.called
    # Verificamos que el tipo de evento se extrajo correctamente
    args, _ = mock_save.call_args
    event_type_detectado = args[0]
    payload_guardado = args[1]

    assert event_type_detectado == "comments"
    assert payload_guardado["object"] == "instagram"


def test_receive_webhook_invalid_structure(client: TestClient):
    """Validate that invalid payloads fail schema validation.

    Args:
        client (TestClient): FastAPI test client fixture.
    """
    payload_invalido = {"object": "instagram", "cosas_raras": []}  # Falta 'entry'

    response = client.post("/webhook", json=payload_invalido)

    assert response.status_code == 422  # Unprocessable Entity
