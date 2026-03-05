"""Repository for reporting queries over webhook logs."""

from datetime import date, timedelta
from sqlalchemy import desc, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog


class MetricsRepository:
    """Query helper for metrics aggregation."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the repository with an async session.

        Args:
            db_session (AsyncSession): Async database session.
        """
        self.db_session = db_session

    async def get_daily_metrics(self, date):
        """Return all webhook logs for a specific date.

        Args:
            date (date): Target date.

        Returns:
            list[WebhookLog]: List of webhook logs.
        """
        result = await self.db_session.execute(
            select(WebhookLog).filter(WebhookLog.received_date == date)
        )
        return result.scalars().all()

    async def get_total_events(self, target_date: date) -> int:
        """Count the total number of events for a given date.

        Args:
            target_date (date): Date to query.

        Returns:
            int: Total event count.
        """
        result = await self.db_session.execute(
            select(func.count())
            .select_from(WebhookLog)
            .filter(func.date(WebhookLog.received_at) == target_date)
        )
        return result.scalar() or 0

    async def get_peak_hour(self, target_date: date) -> dict:
        """Return the hour with the highest activity on the given date.

        Args:
            target_date (date): Date to query.

        Returns:
            dict: Hour and total events, or None if no data.
        """
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
        """Return a summary of events for the last 7 days.

        Returns:
            list[dict]: List of day/total pairs.
        """
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
