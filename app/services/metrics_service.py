"""Metrics service for generating daily and weekly reports."""

import datetime
import logging
from app.repositories.metrics_repositories import MetricsRepository

logger = logging.getLogger(__name__)


class MetricsService:
    """Generate formatted metrics reports using repository data."""

    def __init__(self, db_instance):
        """Initialize the metrics service.

        Args:
            db_instance: Database instance that provides session_factory.
        """
        self.db = db_instance

    async def generate_daily_report(self) -> str:
        """Generate the daily report content.

        Returns:
            str: Report content when data is available, otherwise None.
        """
        today = datetime.date.today()

        # Obtenemos una nueva sesión para esta operación
        async with self.db.session_factory() as session:
            # Creamos el repositorio con esa sesión
            repo = MetricsRepository(session)

            try:
                # Obtenemos los datos
                total_events = await repo.get_total_events(today)
                peak_data = await repo.get_peak_hour(today)

                # Construimos el reporte
                report = f"REPORTE DIARIO DE WEBHOOKS ({today})\n"
                report += "=" * 40 + "\n\n"
                report += f"Total de eventos recibidos hoy: {total_events}\n"

                if peak_data:
                    report += f"Hora pico de actividad: {peak_data['hora']}:00 hrs ({peak_data['total']} eventos)\n"
                else:
                    report += (
                        "No hubo suficiente actividad para determinar hora pico.\n"
                    )

                return report

            except Exception as e:
                logger.error(f"Error generando reporte diario: {e}")
                return None

    async def generate_weekly_report(self) -> str:
        """Generate the weekly report content.

        Returns:
            str: Report content when data is available, otherwise None.
        """
        try:
            async with self.db.session_factory() as session:
                repo = MetricsRepository(session)

                summary = await repo.get_weekly_summary()

                if not summary:
                    return "No hubo actividad en los últimos 7 días."

                report = "RESUMEN SEMANAL DE WEBHOOKS\n"
                report += "=" * 40 + "\n\n"
                report += f"{'Día':<15} | {'Total Eventos'}\n"
                report += "-" * 30 + "\n"

                total_week = 0
                for day in summary:
                    # day es un dict {'dia': 'YYYY-MM-DD', 'total': N}
                    report += f"{day['dia']:<15} | {day['total']}\n"
                    total_week += day["total"]

                report += "\n" + "-" * 30 + "\n"
                report += f"Total semanal: {total_week}\n"

                return report

        except Exception as e:
            logger.error(f"Error generando reporte semanal: {e}")
            return None
