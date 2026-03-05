"""Repository for persisting webhook logs."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_log import WebhookLog


class WebhookLogRepository:
    """Persist webhook logs into the database."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an async session.

        Args:
            session (AsyncSession): Async database session.
        """
        self.session = session

    async def save(self, event_type: str, payload: dict) -> WebhookLog:
        """Save a webhook log entry.

        Args:
            event_type (str): Event type such as "comments" or "messages".
            payload (dict): Full webhook payload.

        Returns:
            WebhookLog: Persisted log entry.
        """
        log = WebhookLog(event_type=event_type, payload=payload)
        self.session.add(log)
        await self.session.commit()
        return log
