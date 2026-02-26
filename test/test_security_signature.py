import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from app.config.settings import settings

def generate_signature(secret: str, payload: dict) -> str:
    """
    Genera manualmente una firma válida para el payload dado.
    Simula lo que hace Meta.
    """
    # request.body() en FastAPI devuelve bytes, así que trabajamos con el JSON stringificado
    # OJO: Los espacios en JSON importan para el hash. FastAPI TestClient envía JSON compacto (sin espacios).
    # Separators=(',', ':') elimina espacios.
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"

def test_signature_validation_success(client: TestClient):
    """
    Prueba completa CON validación de firma activada.
    Generamos firma manual y la enviamos en el header.
    """
    # 1. Activamos validación real
    settings.VERIFY_SIGNATURE = True
    settings.INSTAGRAM_APP_SECRET = "mi_secreto_super_seguro"
    
    payload = {
        "object": "instagram",
        "entry": [{"id": "123", "time": 123456, "changes": [{"field": "comments", "value": "test"}]}]
    }
    
    # serialize as compact json to ensure consistency
    payload_json = json.dumps(payload, separators=(',', ':'))

    # Generate signature for THIS specific string
    signature = hmac.new(
        settings.INSTAGRAM_APP_SECRET.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    
    # Send raw content to ensure it matches exactly valid signature
    response = client.post("/webhook", content=payload_json, headers=headers)

    
    if response.status_code != 200:
        print("Respuesta error:", response.json())

    assert response.status_code == 200
    assert response.json() == {"message": "Webhook recibido"}

def test_signature_validation_failure(client: TestClient):
    """
    Prueba que falle (403) si la firma es incorrecta.
    """
    settings.VERIFY_SIGNATURE = True
    settings.INSTAGRAM_APP_SECRET = "mi_secreto_super_seguro"
    
    payload = {"object": "instagram", "entry": []}
    
    # Firma falsa / de otro payload / o clave incorrecta
    fake_signature = "sha256=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    headers = {"X-Hub-Signature-256": fake_signature}
    response = client.post("/webhook", json=payload, headers=headers)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Token inválido"
