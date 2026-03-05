"""Application entrypoint for the FastAPI webhook service."""

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
