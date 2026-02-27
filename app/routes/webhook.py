import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from app.config.webhook_validator import WebhookPayload
from app.controllers.webhook_processor import WebhookProcessor
from app.controllers.webhook_checker import WebhookChecker
from app.config.db_config import get_db
from app.repositories.webhook_log_repository import WebhookLogRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    """
    Endpoint de verificación de estado.
    Retorna un JSON simple para confirmar que el servicio está activo.
    """
    return {"status": "ok", "message": "Service is alive"}


@router.get("/webhook")
async def root(request: Request):
    """
    Endpoint de verificación para Meta (Instagram/Facebook).

    Maneja el desafío 'hub.challenge' enviado por Meta para confirmar la propiedad del endpoint.
    Valida 'hub.mode' y 'hub.verify_token'.

    Args:
        request (Request): Objeto de solicitud FastAPI para acceder a los query params raw.

    Returns:
        int: El valor de 'hub.challenge' si la verificación es exitosa.

    Raises:
        HTTPException (400): Si faltan parámetros de verificación.
        HTTPException (403): Si el token de verificación es incorrecto (manejado internamente por WebhookChecker).
    """
    # Log completo de lo que Meta realmente envió — útil para depurar
    params = dict(request.query_params)
    logger.info("META GET /webhook solicitud de verificación recibida")

    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")

    if not all([hub_mode, hub_verify_token, hub_challenge]):
        logger.warning(
            f"Parámetros faltantes en verificación de Meta. Keys recibidas: {list(params.keys())}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Parámetros faltantes. Recibidos: {list(params.keys())}",
        )

    checker = WebhookChecker()
    return checker.verify(hub_mode, hub_verify_token, hub_challenge)


@router.post("/webhook")
async def receive_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    db_session=Depends(get_db),
):
    """
    Endpoint principal para recibir notificaciones de webhook de Instagram.

    Flujo:
    1. Valida la firma de seguridad (X-Hub-Signature-256) antes de procesar nada.
    2. Procesa la estructura del payload mediante WebhookProcessor.
    3. Guarda el log crudo en la base de datos de forma asíncrona.
    4. Agenda tareas en segundo plano (_handle_events) para lógica no bloqueante.

    Args:
        payload (WebhookPayload): Cuerpo del mensaje validado por Pydantic.
        background_tasks (BackgroundTasks): Gestor de tareas en segundo plano de FastAPI.
        request (Request): Objeto request para verificar headers de firma.
        db_session: Sesión de base de datos inyectada.

    Returns:
        dict: Mensaje de confirmación.
    """
    repository = WebhookLogRepository(db_session)
    checker = WebhookChecker()
    await checker.verify_signature(request)  # si falla → 403
    processor = WebhookProcessor(payload, repository)
    processor.process()  # si falla → 400
    await processor.save_log()  # persiste antes de responder
    background_tasks.add_task(processor._handle_events)

    return {"message": "Webhook recibido"}
