"""Tests for ReportScheduler behavior."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from app.scheduler.report_scheduler import ReportScheduler


@pytest.fixture
def mock_dependencies():
    """Provide mocked dependencies for scheduler tests."""
    metrics_service = MagicMock()
    # Mockear métodos asíncronos para generar reportes
    metrics_service.generate_daily_report = AsyncMock()
    metrics_service.generate_weekly_report = AsyncMock()

    email_service = MagicMock()
    email_service.send_email = MagicMock()

    return metrics_service, email_service


@pytest.fixture
def scheduler(mock_dependencies):
    """Return a scheduler instance with a mocked APScheduler backend.

    Args:
        mock_dependencies (tuple): Metrics and email service mocks.
    """
    metrics, email = mock_dependencies
    sched = ReportScheduler(metrics, email)
    # Mockear el scheduler interno de APScheduler para no iniciarlo realmente
    sched.scheduler = MagicMock()
    return sched


@pytest.mark.asyncio
async def test_scheduler_jobs_success(scheduler, mock_dependencies):
    """Validate that emails are sent when reports are generated.

    Args:
        scheduler (ReportScheduler): Scheduler under test.
        mock_dependencies (tuple): Metrics and email service mocks.
    """
    metrics_service, email_service = mock_dependencies

    # 1. Test Daily Job Success
    metrics_service.generate_daily_report.return_value = "Daily Report Content"
    await scheduler._daily_job()

    metrics_service.generate_daily_report.assert_awaited_once()
    email_service.send_email.assert_called_once()
    args, kwargs = email_service.send_email.call_args
    assert "Daily Report Content" in kwargs["body"]
    assert "Reporte Diario" in kwargs["subject"]

    # Reset mocks for next test
    email_service.send_email.reset_mock()

    # 2. Test Weekly Job Success
    metrics_service.generate_weekly_report.return_value = "Weekly Report Content"
    await scheduler._weekly_job()

    metrics_service.generate_weekly_report.assert_awaited_once()
    email_service.send_email.assert_called_once()
    args, kwargs = email_service.send_email.call_args
    assert "Weekly Report Content" in kwargs["body"]
    assert "Resumen Semanal" in kwargs["subject"]


@pytest.mark.asyncio
async def test_scheduler_jobs_empty_report(scheduler, mock_dependencies):
    """Validate that emails are not sent for empty reports.

    Args:
        scheduler (ReportScheduler): Scheduler under test.
        mock_dependencies (tuple): Metrics and email service mocks.
    """
    metrics_service, email_service = mock_dependencies

    # 1. Daily Job Empty
    metrics_service.generate_daily_report.return_value = None
    await scheduler._daily_job()
    email_service.send_email.assert_not_called()

    # 2. Weekly Job Empty
    metrics_service.generate_weekly_report.return_value = ""
    await scheduler._weekly_job()
    email_service.send_email.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_jobs_exception(scheduler, mock_dependencies):
    """Ensure exceptions do not crash scheduled jobs.

    Args:
        scheduler (ReportScheduler): Scheduler under test.
        mock_dependencies (tuple): Metrics and email service mocks.
    """
    metrics_service, email_service = mock_dependencies

    # Simular error
    metrics_service.generate_daily_report.side_effect = Exception("DB Connection Error")

    # No debería lanzar excepción
    try:
        await scheduler._daily_job()
    except Exception as e:
        pytest.fail(f"_daily_job failed with exception: {e}")

    email_service.send_email.assert_not_called()


def test_scheduler_start(scheduler):
    """Verify that start() registers jobs and starts the scheduler.

    Args:
        scheduler (ReportScheduler): Scheduler under test.
    """
    scheduler.start()

    # Verificar que se añadieron 2 trabajos
    assert scheduler.scheduler.add_job.call_count == 2

    # Verificar ids
    calls = scheduler.scheduler.add_job.call_args_list
    job_ids = [call.kwargs.get("id") for call in calls]
    assert "daily_report" in job_ids
    assert "weekly_report" in job_ids

    scheduler.scheduler.start.assert_called_once()
