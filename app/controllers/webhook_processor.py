import logging
from fastapi import HTTPException
from app.repositories.webhook_log_repository import WebhookLogRepository
from app.config.webhook_validator import WebhookPayload

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Controlador para procesar eventos de webhook de Instagram.

    Se encarga de validar la estructura básica del payload, identificar el tipo de evento,
    registrar logs informativos y persistir los datos en el repositorio.
    """

    def __init__(self, payload: WebhookPayload, repository: WebhookLogRepository):
        """
        Inicializa el procesador con el payload del webhook y el repositorio de logs.

        Args:
            payload (WebhookPayload): El objeto validado con los datos del webhook.
            repository (WebhookLogRepository): Repositorio para guardar el log en la DB.
        """
        self.payload = payload
        self.repository = repository

    def process(self):
        """
        Valida que el webhook corresponda a un objeto 'instagram' y contenga entradas.

        Raises:
            HTTPException: Si el objeto no es 'instagram' o no hay entradas (entry).

        Returns:
            dict: Mensaje de confirmación de recepción.
        """
        if self.payload.object != "instagram":
            raise HTTPException(
                status_code=400, detail="Objeto no soportado, se esperaba instagram"
            )
        if not self.payload.entry:
            raise HTTPException(status_code=400, detail="Entry vacío en el payload")

        return {"message": "Webhook recibido"}

    def _handle_events(self):
        """
        Tarea en segundo plano para procesar lógica específica de cada evento.

        Itera sobre las entradas y cambios del payload para realizar acciones específicas
        como logging diferenciado según el tipo de campo (comments, mentions, etc.).
        """
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
                    "message_reactions",
                    "message_edit",
                    "messaging_referral",
                    "messaging_optins",
                ]:
                    # Eventos de latido/"visto"/handover comunes que no requieren logueo
                    logger.debug(f"Evento rutinario recibido: {change.field}")
                else:
                    logger.warning(f"Campo no manejado: {change.field}")

    async def save_log(self):
        """
        Guarda el payload del webhook en la base de datos.

        Determina el event_type (ej. "comments") y persiste el payload completo
        como un objeto JSONB crudo utilizando el repositorio.
        """
        event_type = self._extract_event_type()  # "comments" | "messages" | etc.
        raw_payload = self.payload.model_dump()  # dict serializable

        await self.repository.save(event_type, raw_payload)

    def _extract_event_type(self) -> str:
        """
        Extrae el tipo de evento del primer cambio en la primera entrada del payload.

        Returns:
            str: El nombre del campo que cambió (ej. "comments"), o "unknown" si no se encuentra.
        """
        try:
            return self.payload.entry[0].changes[0].field
        except (IndexError, AttributeError):
            return "unknown"
