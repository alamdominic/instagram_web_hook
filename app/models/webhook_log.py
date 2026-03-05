"""SQLAlchemy model for webhook log entries."""

from sqlalchemy import Column, Date, Integer, String, TIMESTAMP, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from app.config.db_config import Base


class WebhookLog(Base):
    """SQLAlchemy model representing the DataLake.webhook_logs table."""

    __tablename__ = "webhook_logs"
    __table_args__ = {"schema": "DataLake"}

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))
    payload = Column(JSONB)
    received_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    received_date = Column(Date, server_default=func.current_date())
    received_time = Column(Time, server_default=func.current_time())

    def __repr__(self):
        """Return a debug-friendly representation of the log entry.

        Returns:
            str: String representation with id and event type.
        """
        return f"<WebhookLog id={self.id} event_type={self.event_type}>"
