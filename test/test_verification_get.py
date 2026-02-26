from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """
    Verifica que el endpoint de salud responda OK.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Service is alive"}

def test_webhook_verification_success(client: TestClient):
    """
    Prueba el 'Handshake' o verificación inicial de Meta.
    Si enviamos el token correcto, debe devolver el challenge.
    """
    # Datos simulando la petición de Meta
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_de_prueba_secreto", # Coincide con conftest.py
        "hub.challenge": "123456789"
    }
    
    response = client.get("/webhook", params=params)
    
    assert response.status_code == 200
    # Meta espera recibir EXACTAMENTE el valor del challenge como texto plano/body
    assert response.text == "123456789"

def test_webhook_verification_invalid_token(client: TestClient):
    """
    Si el token no coincide, debe responder 403 Forbidden.
    """
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_hacker_incorrecto",
        "hub.challenge": "123456789"
    }
    
    response = client.get("/webhook", params=params)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Token inválido"

def test_webhook_verification_missing_params(client: TestClient):
    """
    Si faltan parámetros, debe responder 400 Bad Request.
    """
    # Falta verify_token y challenge
    params = {
        "hub.mode": "subscribe"
    }
    
    response = client.get("/webhook", params=params)
    
    assert response.status_code == 400
