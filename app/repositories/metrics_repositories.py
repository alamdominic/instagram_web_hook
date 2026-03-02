from sqlalchemy import select, func, desc, extract, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog
from datetime import date, timedelta


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

    async def get_total_events(self, target_date: date) -> int:
        """Cuenta el total de eventos recibidos en una fecha."""
        result = await self.db_session.execute(
            select(func.count())
            .select_from(WebhookLog)
            .filter(func.date(WebhookLog.received_at) == target_date)
        )
        return result.scalar() or 0

    async def get_peak_hour(self, target_date: date) -> dict:
        """Determina la hora con más actividad en la fecha dada."""
        result = await self.db_session.execute(
            select(
                extract("hour", WebhookLog.received_at).label("hora"),
                func.count().label("total"),
            )
            .filter(func.date(WebhookLog.received_at) == target_date)
            .group_by("hora")
            .order_by(desc("total"))
            .limit(1)
        )
        row = result.fetchone()
        return {"hora": int(row.hora), "total": row.total} if row else None

    async def get_weekly_summary(self) -> list:
        """Resumen de eventos de los últimos 7 días."""
        result = await self.db_session.execute(
            select(
                func.date(WebhookLog.received_at).label("dia"),
                func.count().label("total"),
            )
            .filter(WebhookLog.received_at >= func.now() - timedelta(days=7))
            .group_by("dia")
            .order_by("dia")
        )
        return [{"dia": str(row.dia), "total": row.total} for row in result.fetchall()]
