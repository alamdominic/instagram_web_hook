"""Controller for processing Instagram webhook events."""

import logging
from fastapi import HTTPException
from app.repositories.webhook_log_repository import WebhookLogRepository
from app.config.webhook_validator import WebhookPayload

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Validate payloads and persist webhook events."""

    def __init__(self, payload: WebhookPayload, repository: WebhookLogRepository):
        """Initialize the processor with payload and repository.

        Args:
            payload (WebhookPayload): Validated webhook payload.
            repository (WebhookLogRepository): Repository used to persist logs.
        """
        self.payload = payload
        self.repository = repository

    def process(self):
        """Validate the minimal payload requirements.

        Returns:
            dict: Confirmation message when validation passes.

        Raises:
            HTTPException: If the object type or entries are invalid.
        """
        if self.payload.object != "instagram":
            raise HTTPException(
                status_code=400, detail="Objeto no soportado, se esperaba instagram"
            )
        if not self.payload.entry:
            raise HTTPException(status_code=400, detail="Entry vacío en el payload")

        return {"message": "Webhook recibido"}

    def _handle_events(self):
        """Handle event-specific processing in background tasks."""
        for entry in self.payload.entry:
            masked_id = self._mask_identifier(entry.id)
            for change in entry.changes:
                if change.field == "comments":
                    logger.info("Nuevo comentario recibido. entry_id=%s", masked_id)
                elif change.field == "mentions":
                    logger.info("Nueva mención recibida. entry_id=%s", masked_id)
                elif change.field == "messages":
                    logger.info("Nuevo mensaje recibido. entry_id=%s", masked_id)
                elif change.field == "stories":
                    logger.info("Nueva historia recibida. entry_id=%s", masked_id)
                elif change.field in [
                    "standby",
                    "messaging_seen",
                    "messaging_handover",
                    "message_reactions",
                    "message_edit",
                    "messaging_referral",
                    "messaging_optins",
                ]:
                    # Eventos de latido/"visto"/handover comunes que no requieren logueo
                    logger.debug(f"Evento rutinario recibido: {change.field}")
                else:
                    logger.warning(f"Campo no manejado: {change.field}")

    @staticmethod
    def _mask_identifier(value: str, visible: int = 4) -> str:
        """Mask an identifier for safe logging.

        Args:
            value (str): Identifier to mask.
            visible (int): Number of trailing characters to keep.

        Returns:
            str: Masked identifier.
        """
        if not value:
            return ""
        if len(value) <= visible:
            return "*" * len(value)
        return f"{'*' * (len(value) - visible)}{value[-visible:]}"

    async def save_log(self):
        """Persist the raw webhook payload in the database."""
        event_type = self._extract_event_type()  # "comments" | "messages" | etc.
        raw_payload = self.payload.model_dump()  # dict serializable

        await self.repository.save(event_type, raw_payload)

    def _extract_event_type(self) -> str:
        """Extract the event type from the first entry.

        Returns:
            str: Field name such as "comments", or "unknown" if unavailable.
        """
        try:
            return self.payload.entry[0].changes[0].field
        except (IndexError, AttributeError):
            return "unknown"
