"""Pytest fixtures and dependency overrides for the test suite."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings
from app.config.db_config import get_db


async def override_get_db():
    """Provide a mocked async DB session for tests.

    Yields:
        AsyncMock: Mocked async database session.
    """
    mock_session = AsyncMock()
    # Cuando se llame a commit, no hace nada (éxito inmediato)
    mock_session.commit = AsyncMock()
    mock_session.add = MagicMock()
    yield mock_session


# Aplicamos el override a la dependencia de FastAPI
app.dependency_overrides[get_db] = override_get_db


# 2. Cliente de Pruebas
@pytest.fixture
def client():
    """Return a synchronous HTTP client for API tests.

    Returns:
        TestClient: FastAPI test client.
    """
    return TestClient(app)


# 3. Configuración de Prueba
@pytest.fixture(autouse=True)
def mock_settings():
    """Override settings for deterministic tests.

    Yields:
        None: Control back to the test and then restore settings.
    """
    original_verify_token = settings.INSTAGRAM_VERIFY_TOKEN
    original_app_secret = settings.INSTAGRAM_APP_SECRET
    original_signature_check = settings.VERIFY_SIGNATURE

    # Valores conocidos para los tests
    settings.INSTAGRAM_VERIFY_TOKEN = "token_de_prueba_secreto"
    settings.INSTAGRAM_APP_SECRET = "secret_12345"  # Usado para firmar
    settings.VERIFY_SIGNATURE = (
        False  # Por defecto apagado para facilitar tests lógicos
    )

    yield

    # Restaurar valores originales al terminar
    settings.INSTAGRAM_VERIFY_TOKEN = original_verify_token
    settings.INSTAGRAM_APP_SECRET = original_app_secret
    settings.VERIFY_SIGNATURE = original_signature_check
