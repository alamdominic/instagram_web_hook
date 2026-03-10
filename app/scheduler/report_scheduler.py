"""Scheduler for periodic metrics reports."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Schedule daily and weekly report jobs."""

    def __init__(self, metrics_service, email_service):
        """Initialize the scheduler with report dependencies.

        Args:
            metrics_service: Metrics service used to build reports.
            email_service: Email service used to send reports.
        """
        self.metrics_service = metrics_service
        self.email_service = email_service
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Register and start scheduled jobs."""
        # Reporte diario: Se ejecuta todos los días a las 7:00 AM México ≈ 13:00 UTC (hora estándar)
        self.scheduler.add_job(
            self._daily_job,
            CronTrigger(hour=13, minute=00, timezone="UTC"),
            id="daily_report",
            replace_existing=True,
        )

        # Reporte semanal: Se ejecuta todos los lunes a las 7:00 AM México ≈ 13:00 UTC (hora estándar)
        self.scheduler.add_job(
            self._weekly_job,
            CronTrigger(day_of_week="mon", hour=13, minute=00, timezone="UTC"),
            id="weekly_report",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("ReportScheduler iniciado correctamente.")

    async def _daily_job(self):
        """Generate and send the daily report."""
        try:
            logger.info("Iniciando generación de reporte diario...")
            # Asumimos que metrics_service tiene este método
            report_content = await self.metrics_service.generate_daily_report()

            if report_content:
                self.email_service.send_email(
                    subject="Reporte Diario de Webhooks", body=report_content
                )
                logger.info("Reporte diario enviado exitosamente.")
            else:
                logger.warning("El reporte diario estaba vacío, no se envió correo.")
        except Exception as e:
            logger.error(f"Error en _daily_job: {e}")

    async def _weekly_job(self):
        """Generate and send the weekly report."""
        try:
            logger.info("Iniciando generación de reporte semanal...")
            # Asumimos que metrics_service tiene este método
            report_content = await self.metrics_service.generate_weekly_report()

            if report_content:
                self.email_service.send_email(
                    subject="Resumen Semanal de Webhooks", body=report_content
                )
                logger.info("Reporte semanal enviado exitosamente.")
            else:
                logger.warning("El reporte semanal estaba vacío, no se envió correo.")
        except Exception as e:
            logger.error(f"Error en _weekly_job: {e}")
