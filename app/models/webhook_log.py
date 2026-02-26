# app/models/webhook_log.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from app.config.db_config import Base


class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    __table_args__ = {"schema": "DataLake"}

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))
    payload = Column(JSONB)
    received_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    """
        Es un método opcional de Python que define cómo se muestra el objeto cuando lo imprimes o lo ves en el debugger.
        En lugar de ver una dirección de memoria ilegible, ves información útil del objeto.
    """

    def __repr__(self):
        return f"<WebhookLog id={self.id} event_type={self.event_type}>"
