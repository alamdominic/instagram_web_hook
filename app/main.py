import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routes.webhook import router as webhook_router
from app.config.db_config import db
from app.config.settings import settings
from app.services.email_service import EmailService
from app.services.metrics_service import MetricsService
from app.scheduler.report_scheduler import ReportScheduler

# Configuración básica de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ejecuta código automáticamente cuando el servidor arranca.
    Es como un "gancho" de inicio.
    """
    # 1. Verificar conexión a DB
    await db.check_connection()
    
    # 2. Inicializar servicios
    email_service = EmailService(settings)
    metrics_service = MetricsService(db)  # Pasamos la instancia de DB factory
    
    # 3. Inicializar y arrancar scheduler
    scheduler = ReportScheduler(metrics_service, email_service)
    scheduler.start()
    
    logger.info("Aplicación iniciada correctamente con Scheduler activo.")
    
    yield
    
    # Aquí iría lógica de limpieza al cerrar (shutdown)
    if scheduler.scheduler.running:
        scheduler.scheduler.shutdown()
        logger.info("Scheduler detenido.")

app = FastAPI(lifespan=lifespan)

app.include_router(webhook_router)
