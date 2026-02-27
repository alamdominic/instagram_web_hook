# app/repositories/webhook_log_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog


class WebhookLogRepository:
    """
    Repositorio encargado de la persistencia de logs de webhooks en la base de datos.

    Responsabilidad única: persistir logs en la DB.
    No valida, no transforma, no procesa.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos asíncrona.

        Args:
            session (AsyncSession): Sesión de SQLAlchemy para interactuar con la DB.
        """
        self.session = session

    async def save(self, event_type: str, payload: dict) -> WebhookLog:
        """
        Guarda un nuevo registro de webhook en la base de datos.

        Crea una instancia de WebhookLog, la añade a la sesión y realiza el commit.

        Args:
            event_type (str): El tipo de evento (ej. "comments", "messages").
            payload (dict): El contenido completo del webhook en formato diccionario.

        Returns:
            WebhookLog: La instancia del log guardado con su ID generado.
        """
        log = WebhookLog(event_type=event_type, payload=payload)
        self.session.add(log)
        await self.session.commit()
        return log
