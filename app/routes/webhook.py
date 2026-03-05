"""HTTP routes for health checks and Instagram webhook handling."""

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from app.config.webhook_validator import WebhookPayload
from app.controllers.webhook_checker import WebhookChecker
from app.controllers.webhook_processor import WebhookProcessor
from app.config.db_config import get_db
from app.repositories.webhook_log_repository import WebhookLogRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    """Return a simple health status payload.

    Returns:
        dict: Health status response.
    """
    return {"status": "ok", "message": "Service is alive"}


@router.get("/webhook")
async def root(request: Request):
    """Handle the GET verification handshake from Meta.

    Args:
        request (Request): Request object used to access query params.

    Returns:
        Response: Plain text response with the hub challenge.

    Raises:
        HTTPException: If parameters are missing or the token is invalid.
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
    """Receive and process a webhook payload.

    Args:
        payload (WebhookPayload): Validated webhook payload.
        background_tasks (BackgroundTasks): FastAPI background task manager.
        request (Request): Raw request used for signature validation.
        db_session: Database session injected by dependency.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If signature or payload validation fails.
    """
    repository = WebhookLogRepository(db_session)
    checker = WebhookChecker()
    await checker.verify_signature(request)  # si falla → 403
    processor = WebhookProcessor(payload, repository)
    processor.process()  # si falla → 400
    await processor.save_log()  # persiste antes de responder
    background_tasks.add_task(processor._handle_events)

    return {"message": "Webhook recibido"}
