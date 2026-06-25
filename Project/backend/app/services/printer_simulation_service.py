import asyncio
import logging
import random
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.audit_log import AuditLog
from app.models.print_job import JobStatus, PrintJob
from app.models.printer import Printer, PrinterStatus
from app.core.tokens import generate_collection_code

logger = logging.getLogger(__name__)


class PrinterSimulationService:
    async def simulate_job_printing(self, job_id: int) -> bool:
        """
        Attempts to assign a printer and simulate printing for a print job.
        Returns True if the job was printed or failed permanently.
        Returns False if no printer was available (so the task should be retried).
        """
        # We import here to avoid circular imports
        from app.services.analytics_service import invalidate_analytics_cache
        from app.services.notification_service import (
            notify_job_status,
            publish_job_status_update,
        )
        from app.services.queue_service import queue_service

        async with async_session() as db:
            result = await db.execute(
                select(PrintJob)
                .options(selectinload(PrintJob.user))
                .where(PrintJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                logger.error(f"Simulation: Job {job_id} not found in database.")
                return True

            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(
                    f"Simulation: Job {job_id} is already in final status {job.status}."
                )
                return True

            # Find an ONLINE active printer supporting the required configuration
            printer_query = select(Printer).where(
                Printer.is_active == True,  # noqa: E712
                Printer.status == PrinterStatus.ONLINE,
            )
            if job.is_color:
                printer_query = printer_query.where(Printer.supports_color == True)  # noqa: E712
            if job.is_double_sided:
                printer_query = printer_query.where(Printer.supports_duplex == True)  # noqa: E712

            printer_query = printer_query.order_by(
                Printer.health_score.desc(), Printer.jobs_completed.asc()
            )
            printer_result = await db.execute(printer_query)
            printers = printer_result.scalars().all()

            if not printers:
                logger.info(
                    f"Simulation: No available ONLINE printer for Job {job_id}. Will retry."
                )
                return False

            printer = printers[0]

            # Assign printer and set status to BUSY
            job.printer_id = printer.id
            job.status = JobStatus.PRINTING
            printer.status = PrinterStatus.BUSY

            # Audit start
            audit = AuditLog(
                user_id=job.user_id,
                action="PRINT_START",
                target_type="print_job",
                target_id=job.id,
                details={"printer_id": printer.id, "printer_name": printer.name},
            )
            db.add(audit)

            await notify_job_status(db, job, job.user.email, "printing")
            await publish_job_status_update(
                job.user_id, job.id, "printing", {"printer_name": printer.name}
            )
            await db.commit()

            logger.info(
                f"Simulation: Printer '{printer.name}' assigned to Job {job.id}. Printing started."
            )

        # Simulate printing duration (0.5 seconds per page)
        print_duration = max(1, job.pages_to_print * 0.5)
        await asyncio.sleep(print_duration)

        # Handle completion/failure in a new session to ensure isolation
        async with async_session() as db_complete:
            job = await db_complete.get(PrintJob, job_id)
            printer = await db_complete.get(Printer, printer.id)

            # Simulated hardware failure / paper jam (5% chance)
            is_failed = random.random() < 0.05
            if is_failed:
                logger.warning(
                    f"Simulation: Hardware failure on Printer '{printer.name}' during Job {job.id}."
                )
                printer.jobs_failed += 1
                printer.health_score = max(0.0, printer.health_score - 15.0)

                audit = AuditLog(
                    user_id=job.user_id,
                    action="PRINT_FAILURE",
                    target_type="print_job",
                    target_id=job.id,
                    details={
                        "printer_id": printer.id,
                        "printer_name": printer.name,
                        "health_score": printer.health_score,
                    },
                )
                db_complete.add(audit)

                if printer.health_score < 20.0:
                    printer.status = PrinterStatus.MAINTENANCE
                    logger.warning(
                        f"Simulation: Printer '{printer.name}' health score fell below 20. Set to MAINTENANCE."
                    )
                else:
                    printer.status = PrinterStatus.ONLINE

                job.retry_count += 1
                if job.retry_count <= 3:
                    job.status = JobStatus.QUEUED
                    await notify_job_status(db_complete, job, job.user.email, "queued")
                    await publish_job_status_update(
                        job.user_id,
                        job.id,
                        "queued",
                        {"message": f"Job failed, retrying (attempt {job.retry_count})"},
                    )
                    await queue_service.enqueue(
                        job.id, job.priority_score, {"retry": job.retry_count}
                    )
                    logger.info(f"Simulation: Job {job.id} requeued.")
                else:
                    job.status = JobStatus.FAILED
                    await notify_job_status(db_complete, job, job.user.email, "failed")
                    await publish_job_status_update(
                        job.user_id, job.id, "failed", {"message": "Max retries reached"}
                    )
                    logger.error(
                        f"Simulation: Job {job.id} permanently failed after max retries."
                    )
            else:
                # Printing succeeded
                printer.jobs_completed += 1
                printer.status = PrinterStatus.ONLINE
                job.status = JobStatus.COMPLETED
                job.collection_code = generate_collection_code()

                audit = AuditLog(
                    user_id=job.user_id,
                    action="PRINT_SUCCESS",
                    target_type="print_job",
                    target_id=job.id,
                    details={"printer_id": printer.id, "collection_code": job.collection_code},
                )
                db_complete.add(audit)

                await notify_job_status(db_complete, job, job.user.email, "completed")
                await publish_job_status_update(
                    job.user_id, job.id, "completed", {"collection_code": job.collection_code}
                )
                logger.info(
                    f"Simulation: Job {job.id} printed successfully on '{printer.name}'."
                )

            await db_complete.commit()
            await invalidate_analytics_cache()

        return True


printer_simulation_service = PrinterSimulationService()
