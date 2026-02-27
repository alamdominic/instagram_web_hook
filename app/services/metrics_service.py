# app/repositories/metrics_repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog
from datetime import date


class MetricsRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_total_events(self, target_date: date) -> int:
        # EQUIVALENTE A "SELECT COUNT(*) FROM SCHEMA.TABLE WHERE DATE(received_at) = :target_date"
        result = await self.db_session.execute(
            select(func.count())
            .select_from(WebhookLog)
            .filter(func.date(WebhookLog.received_at) == target_date)
        )
        return result.scalar()

    async def get_peak_hour(self, target_date: date) -> dict:
        # EQUIVALENTE A "SELECT EXTRACT(HOUR FROM received_at) AS hora, COUNT(*) AS total FROM SCHEMA.TABLE WHERE DATE(received_at) = :target_date GROUP BY hora ORDER BY total DESC LIMIT 1"
        result = await self.db_session.execute(
            select(
                func.extract("hour", WebhookLog.received_at).label("hora"),
                func.count().label("total"),
            )
            .filter(func.date(WebhookLog.received_at) == target_date)
            .group_by("hora")
            .order_by(func.count().desc())
            .limit(1)
        )
        row = result.fetchone()
        return {"hora": int(row.hora), "total": row.total} if row else None

    async def get_weekly_summary(self) -> list:
        # EQUIVALENTE A "SELECT DATE(received_at) AS dia, COUNT(*) AS total FROM SCHEMA.TABLE WHERE received_at >= NOW() - INTERVAL '7 days' GROUP BY dia ORDER BY dia"
        result = await self.db_session.execute(
            select(
                func.date(WebhookLog.received_at).label("dia"),
                func.count().label("total"),
            )
            .filter(
                WebhookLog.received_at >= func.now() - func.cast("7 days", type_=None)
            )
            .group_by("dia")
            .order_by("dia")
        )
        return [{"dia": str(row.dia), "total": row.total} for row in result.fetchall()]
