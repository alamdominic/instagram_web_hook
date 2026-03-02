import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Clase para programar tareas de generación y envío de reportes.
    ├── __init__(metrics_service)
    ├── start()
    ├── _daily_job()
    └── _weekly_job()"""

    def __init__(self, metrics_service, email_service):
        """Inicializa el scheduler con el servicio de métricas y el servicio de correo.

        Args:A
            metrics_service: Servicio de métricas para obtener datos.
            email_service: Servicio de correo para enviar reportes.
        """
        self.metrics_service = metrics_service
        self.email_service = email_service
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Inicia el planificador de tareas."""
        # Reporte diario: Se ejecuta todos los días a las 8:00 AM
        self.scheduler.add_job(
            self._daily_job,
            CronTrigger(hour=20, minute=10),
            id="daily_report",
            replace_existing=True,
        )

        # Reporte semanal: Se ejecuta todos los lunes a las 9:00 AM
        self.scheduler.add_job(
            self._weekly_job,
            CronTrigger(day_of_week="mon", hour=20, minute=10),
            id="weekly_report",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("ReportScheduler iniciado correctamente.")

    async def _daily_job(self):
        """Genera y envía el reporte diario."""
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
        """Genera y envía el reporte semanal."""
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
