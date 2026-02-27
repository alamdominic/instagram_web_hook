# app/models/webhook_log.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, Date, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from app.config.db_config import Base


class WebhookLog(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'webhook_logs' en la base de datos.
    Esta tabla almacena los registros crudos de los webhooks recibidos.
    """

    __tablename__ = "webhook_logs"
    __table_args__ = {"schema": "DataLake"}

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))
    payload = Column(JSONB)
    received_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    received_date = Column(Date, server_default=func.current_date())
    received_time = Column(Time, server_default=func.current_time())

    def __repr__(self):
        """
        Representación de cadena del objeto para depuración.
        Muestra el ID y el tipo de evento del log.
        """
        return f"<WebhookLog id={self.id} event_type={self.event_type}>"
