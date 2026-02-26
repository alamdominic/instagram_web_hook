# app/repositories/webhook_log_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog


class WebhookLogRepository:
    """
    Responsabilidad única: persistir logs en la DB.
    No valida, no transforma, no procesa.
    AsyncSession se inyecta, no se crea aquí — el repositorio no sabe nada de cómo se conecta a la DB,
    Eso es el principio de inversión de dependencias (DIP) en práctica.
    self.session.add(log) — le dice a SQLAlchemy "trackea este objeto", pero aún no escribe en la DB.
    await self.session.commit() — aquí es cuando realmente se ejecuta el INSERT en PostgreSQL.
    Es async porque no queremos bloquear el servidor mientras espera respuesta de la DB.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event_type: str, payload: dict) -> WebhookLog:
        log = WebhookLog(event_type=event_type, payload=payload)
        self.session.add(log)
        await self.session.commit()
        return log
