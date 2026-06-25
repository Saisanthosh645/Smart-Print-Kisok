import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.rate_limiter import RateLimiter
from app.models.print_job import JobStatus, PrintJob
from app.models.printer import Printer, PrinterStatus
from app.services.printer_simulation_service import printer_simulation_service


# Test Rate Limiting
def test_rate_limiter_not_connected_redis():
    """Verify rate limiter allows requests when Redis is not initialized."""
    limiter = RateLimiter(times=1, seconds=10)
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {}
    mock_request.url.path = "/test-route"

    # When Redis is not available, calling the limiter shouldn't raise 429
    with patch("app.services.queue_service.queue_service.redis", new_callable=PropertyMock) as mock_redis_prop:
        mock_redis_prop.side_effect = RuntimeError("Redis not connected")
        # Should execute without raising HTTPException
        asyncio.run(limiter(mock_request))


class PropertyMock(MagicMock):
    def __get__(self, instance, owner):
        return self()


@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    """Verify rate limiter raises 429 when Redis limits are exceeded."""
    limiter = RateLimiter(times=2, seconds=10)
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {}
    mock_request.url.path = "/test-route"

    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "2"  # Limit exceeded
    mock_redis.ttl.return_value = 5

    with patch("app.services.queue_service.queue_service._redis", mock_redis):
        with pytest.raises(Exception) as exc_info:
            await limiter(mock_request)
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Too many requests" in exc_info.value.detail


# Test Print Job Simulation
@pytest.mark.asyncio
async def test_printer_simulation_no_printers():
    """Test that simulation returns False when no online printer is found."""
    # Mock database session to return no printers
    mock_db = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    
    mock_job = PrintJob(
        id=1,
        user_id=1,
        pages_to_print=5,
        status=JobStatus.QUEUED,
        is_color=False,
        is_double_sided=False,
        priority_score=10.0
    )
    mock_job_result = MagicMock()
    mock_job_result.scalar_one_or_none.return_value = mock_job

    mock_db.execute = AsyncMock()
    # First query for job, second query for printers
    mock_db.execute.side_effect = [mock_job_result, mock_result]

    with patch("app.services.printer_simulation_service.async_session") as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value = mock_db
        success = await printer_simulation_service.simulate_job_printing(job_id=1)
        # Should return False (triggers retry in worker) because no printers are online
        assert success is False


@pytest.mark.asyncio
async def test_printer_simulation_success():
    """Test successful printer assignment and state transitions."""
    mock_db = MagicMock()
    
    mock_job = MagicMock(spec=PrintJob)
    mock_job.id = 1
    mock_job.user_id = 1
    mock_job.pages_to_print = 2
    mock_job.status = JobStatus.QUEUED
    mock_job.is_color = False
    mock_job.is_double_sided = False
    mock_job.priority_score = 10.0
    mock_job.user = MagicMock()
    mock_job.user.email = "student@demo.com"

    mock_printer = MagicMock(spec=Printer)
    mock_printer.id = 1
    mock_printer.name = "Kiosk A1"
    mock_printer.status = PrinterStatus.ONLINE
    mock_printer.jobs_completed = 0
    mock_printer.jobs_failed = 0
    mock_printer.health_score = 100.0

    mock_job_result = MagicMock()
    mock_job_result.scalar_one_or_none.return_value = mock_job

    mock_printer_scalars = MagicMock()
    mock_printer_scalars.all.return_value = [mock_printer]
    mock_printer_result = MagicMock()
    mock_printer_result.scalars.return_value = mock_printer_scalars

    mock_db.execute = AsyncMock()
    mock_db.execute.side_effect = [mock_job_result, mock_printer_result]
    mock_db.commit = AsyncMock()

    # Mock async sleep and notifications/pubsub to prevent actual processing delay
    with patch("app.services.printer_simulation_service.async_session") as mock_session_maker, \
         patch("app.services.printer_simulation_service.asyncio.sleep", AsyncMock()) as mock_sleep, \
         patch("app.services.notification_service.notify_job_status", AsyncMock()) as mock_notify, \
         patch("app.services.notification_service.publish_job_status_update", AsyncMock()) as mock_pubsub, \
         patch("app.services.analytics_service.invalidate_analytics_cache", AsyncMock()) as mock_cache_inv, \
         patch("random.random", return_value=0.5): # force success (random > 0.05)
         
        mock_session_maker.return_value.__aenter__.return_value = mock_db
        mock_db.get = AsyncMock()
        mock_db.get.side_effect = [mock_job, mock_printer]

        success = await printer_simulation_service.simulate_job_printing(job_id=1)
        
        # Verify job was completed successfully and printer set back to ONLINE
        assert success is True
        assert mock_job.status == JobStatus.COMPLETED
        assert mock_printer.status == PrinterStatus.ONLINE
        assert mock_printer.jobs_completed == 1
