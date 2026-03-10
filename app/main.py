"""
Application entrypoint for the FastAPI webhook service.

Este módulo configura e inicializa la aplicación FastAPI para el servicio de webhooks.

Funcionalidades implementadas:
-----------------------------
1. CONFIGURACIÓN DE LOGGING:
   - Configuración básica de logs con formato timestamp, nivel y nombre del logger.
   - Nivel de logging establecido en INFO.

2. CICLO DE VIDA DE LA APLICACIÓN (lifespan):
   - Startup:
     * Verificación de conexión a base de datos (db.check_connection).
     * Inicialización del servicio de email (EmailService).
     * Inicialización del servicio de métricas (MetricsService).
     * Inicialización y arranque del programador de reportes (ReportScheduler).
   - Shutdown:
     * Detención del scheduler si está corriendo.

3. CONFIGURACIÓN DE FastAPI:
   - Instancia de FastAPI con gestión de ciclo de vida mediante lifespan.
   - Middleware de rate limiting (100 requests por ventana de 60 segundos).
   - Router de webhooks incluido para manejar las rutas del servicio.

Dependencias:
-------------
- app.middleware.rate_limiter: Middleware para limitar tasa de peticiones.
- app.routes.webhook: Router con endpoints del webhook.
- app.config.db_config: Configuración y conexión a base de datos.
- app.config.settings: Configuración general de la aplicación.
- app.services.email_service: Servicio para envío de emails.
- app.services.metrics_service: Servicio para gestión de métricas.
- app.scheduler.report_scheduler: Programador de reportes automáticos.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.middleware.rate_limiter import RateLimiterMiddleware
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
    """Run startup and shutdown routines for the application.

    Args:
        app (FastAPI): FastAPI application instance.

    Yields:
        None: Control back to FastAPI during application lifetime.
    """
    # 1. Verify DB connection
    await db.check_connection()

    # 2. Initialize services
    email_service = EmailService(settings)
    metrics_service = MetricsService(db)  # DB factory instance

    # 3. Initialize and start scheduler
    scheduler = ReportScheduler(metrics_service, email_service)
    scheduler.start()

    logger.info("Application started with active scheduler.")

    yield

    # Cleanup on shutdown
    if scheduler.scheduler.running:
        scheduler.scheduler.shutdown()
        logger.info("Scheduler stopped.")


app = FastAPI(lifespan=lifespan)
app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=60)
app.include_router(webhook_router)
