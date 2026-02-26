import logging
from fastapi import HTTPException
from app.repositories.webhook_log_repository import WebhookLogRepository
from app.config.webhook_validator import WebhookPayload

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Controlador para manejar los eventos del webhook de Instagram.
    Aquí se implementaría la lógica para manejar los eventos que Instagram envía al webhook.
    Por ejemplo, podríamos leer el payload, validar la firma, y luego procesar los datos.
    """

    def __init__(self, payload: WebhookPayload, repository: WebhookLogRepository):
        self.payload = payload
        self.repository = repository

    def process(self):
        if self.payload.object != "instagram":
            raise HTTPException(
                status_code=400, detail="Objeto no soportado, se esperaba instagram"
            )
        if not self.payload.entry:
            raise HTTPException(status_code=400, detail="Entry vacío en el payload")

        return {"message": "Webhook recibido"}

    def _handle_events(self):
        for entry in self.payload.entry:
            for change in entry.changes:
                if change.field == "comments":
                    logger.info(f"Nuevo comentario recibido. ID: {entry.id}")
                elif change.field == "mentions":
                    logger.info(f"Nueva mención recibida. ID: {entry.id}")
                elif change.field == "messages":
                    logger.info(f"Nuevo mensaje recibido. ID: {entry.id}")
                elif change.field == "stories":
                    logger.info(f"Nueva historia recibida. ID: {entry.id}")
                elif change.field in [
                    "standby",
                    "messaging_seen",
                    "messaging_handover",
                ]:
                    # Eventos de latido/"visto"/handover comunes que no requieren logueo
                    logger.debug(f"Evento rutinario recibido: {change.field}")
                else:
                    logger.warning(f"Campo no manejado: {change.field}")

    async def save_log(self):
        """
        Determina el event_type leyendo el primer change del primer entry.
        Persiste el payload completo como JSONB crudo → el ETL limpia después.
        """
        event_type = self._extract_event_type()  # "comments" | "messages" | etc.
        raw_payload = self.payload.model_dump()  # dict serializable

        await self.repository.save(event_type, raw_payload)

    def _extract_event_type(self) -> str:
        try:
            return self.payload.entry[0].changes[0].field
        except (IndexError, AttributeError):
            return "unknown"
