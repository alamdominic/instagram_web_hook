"""Tests for MetricsService report generation."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.metrics_service import MetricsService


@pytest.mark.asyncio
async def test_generate_daily_report(mocker):
    """Validate the daily report format and repository calls.

    Args:
        mocker: Pytest mocker fixture.
    """
    # 1. Mock Repository class calls
    mock_repo_instance = AsyncMock()
    mock_repo_instance.get_total_events.return_value = 100
    mock_repo_instance.get_peak_hour.return_value = {"hora": 14, "total": 50}

    # Patch the class where it is IMPORTED (metrics_service)
    mocker.patch(
        "app.services.metrics_service.MetricsRepository",
        return_value=mock_repo_instance,
    )

    # 2. Mock DB
    mock_db = MagicMock()
    mock_session = AsyncMock()
    # Mock context manager behavior for session_factory
    mock_db.session_factory.return_value.__aenter__.return_value = mock_session

    # 3. Test
    service = MetricsService(mock_db)
    report = await service.generate_daily_report()

    assert "REPORTE DIARIO DE WEBHOOKS" in report
    assert "100" in report
    assert "14:00" in report

    # Verify interaction
    mock_repo_instance.get_total_events.assert_called_once()
    mock_db.session_factory.assert_called_once()


@pytest.mark.asyncio
async def test_generate_weekly_report(mocker):
    """Validate the weekly report formatting and totals.

    Args:
        mocker: Pytest mocker fixture.
    """
    # 1. Mock Repository
    mock_repo_instance = AsyncMock()
    mock_repo_instance.get_weekly_summary.return_value = [
        {"dia": date(2023, 1, 1), "total": 10},
        {"dia": date(2023, 1, 2), "total": 20},
    ]

    mocker.patch(
        "app.services.metrics_service.MetricsRepository",
        return_value=mock_repo_instance,
    )

    # 2. Mock DB
    mock_db = MagicMock()
    mock_session = AsyncMock()
    mock_db.session_factory.return_value.__aenter__.return_value = mock_session

    # 3. Test
    service = MetricsService(mock_db)
    report = await service.generate_weekly_report()

    assert "RESUMEN SEMANAL DE WEBHOOKS" in report
    assert "30" in report  # 10 + 20
