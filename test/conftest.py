import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings
from app.config.db_config import get_db

# 1. Mock de Base de Datos
# Evitamos conectar a la base de datos real durante los tests
async def override_get_db():
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
    """
    Cliente HTTP síncrono para probar los endpoints.
    FastAPI TestClient usa 'requests' por debajo.
    """
    return TestClient(app)

# 3. Configuración de Prueba
@pytest.fixture(autouse=True)
def mock_settings():
    """
    Sobrescribe configuraciones críticas para que los tests sean predecibles.
    """
    original_verify_token = settings.INSTAGRAM_VERIFY_TOKEN
    original_app_secret = settings.INSTAGRAM_APP_SECRET
    original_signature_check = settings.VERIFY_SIGNATURE

    # Valores conocidos para los tests
    settings.INSTAGRAM_VERIFY_TOKEN = "token_de_prueba_secreto"
    settings.INSTAGRAM_APP_SECRET = "secret_12345" # Usado para firmar
    settings.VERIFY_SIGNATURE = False # Por defecto apagado para facilitar tests lógicos

    yield

    # Restaurar valores originales al terminar
    settings.INSTAGRAM_VERIFY_TOKEN = original_verify_token
    settings.INSTAGRAM_APP_SECRET = original_app_secret
    settings.VERIFY_SIGNATURE = original_signature_check
