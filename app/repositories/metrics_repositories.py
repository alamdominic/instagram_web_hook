from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog


class MetricsRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_daily_metrics(self, date):
        """
        Obtiene las métricas del día especificado.
        EQUIVALENTE A "SELECT * FROM SCHEMA.TABLE WHERE received_date = :date"
        """
        result = await self.db_session.execute(
            select(WebhookLog).filter(WebhookLog.received_date == date)
        )
        return result.scalars().all()
