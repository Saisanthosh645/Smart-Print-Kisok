import asyncio
import logging

from app.core.celery_app import celery_app
from app.services.printer_simulation_service import printer_simulation_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.process_print_job", max_retries=None)
def process_print_job(self, job_id: int):
    logger.info(f"Celery worker received print job {job_id}")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    success = loop.run_until_complete(
        printer_simulation_service.simulate_job_printing(job_id)
    )

    if not success:
        logger.info(
            f"No printer available for Job {job_id}. Re-scheduling print task in 5 seconds."
        )
        raise self.retry(countdown=5)
