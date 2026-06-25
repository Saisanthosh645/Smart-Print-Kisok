import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_roles
from app.core.tokens import generate_collection_code
from app.database import get_db
from app.core.pagination import paginate
from app.models.print_job import JobStatus, PrintJob
from app.models.printer import Printer, PrinterStatus
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas import PrintJobResponse, PrinterResponse, PaginatedPrintJobs
from app.services.notification_service import assign_printer, notify_job_status
from app.services.queue_service import queue_service
from app.services.analytics_service import invalidate_analytics_cache

router = APIRouter(prefix="/print-center", tags=["print-center"])
logger = logging.getLogger(__name__)


@router.get("/jobs", response_model=PaginatedPrintJobs)
async def incoming_jobs(
    page: int = 1,
    size: int = 20,
    _: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(PrintJob)
        .options(selectinload(PrintJob.document), selectinload(PrintJob.user))
        .where(PrintJob.status.in_([JobStatus.QUEUED, JobStatus.PRINTING, JobStatus.PROCESSING]))
        .order_by(PrintJob.priority_score.asc())
    )
    return await paginate(db, query, page, size)


@router.get("/queue")
async def priority_queue(
    _: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
):
    items = await queue_service.peek_all(50)
    return {"queue_size": await queue_service.size(), "jobs": [{"job_id": jid, "priority": p} for jid, p in items]}


@router.post("/jobs/{job_id}/assign")
async def assign_job_to_printer(
    job_id: int,
    operator: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PrintJob).where(PrintJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    printer = await assign_printer(db, job)
    if not printer:
        raise HTTPException(status_code=503, detail="No available printers")

    audit = AuditLog(
        user_id=operator.id,
        action="OPERATOR_ASSIGN_PRINTER",
        target_type="print_job",
        target_id=job.id,
        details={"printer_id": printer.id, "printer_name": printer.name},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"job_id": job.id, "printer_id": printer.id, "printer_name": printer.name}


@router.post("/jobs/{job_id}/start")
async def start_printing(
    job_id: int,
    operator: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.user), selectinload(PrintJob.document))
        .where(PrintJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.printer_id:
        await assign_printer(db, job)

    job.status = JobStatus.PRINTING
    await notify_job_status(db, job, job.user.email, "printing")

    audit = AuditLog(
        user_id=operator.id,
        action="OPERATOR_START_PRINT",
        target_type="print_job",
        target_id=job.id,
        details={"printer_id": job.printer_id},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return job


@router.post("/jobs/{job_id}/complete")
async def complete_job(
    job_id: int,
    operator: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.user), selectinload(PrintJob.document))
        .where(PrintJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.COMPLETED
    job.collection_code = generate_collection_code()
    await notify_job_status(db, job, job.user.email, "completed")
    await queue_service.remove(job.id)

    if job.printer_id:
        printer_result = await db.execute(select(Printer).where(Printer.id == job.printer_id))
        printer = printer_result.scalar_one_or_none()
        if printer:
            printer.jobs_completed += 1
            printer.status = PrinterStatus.ONLINE

    audit = AuditLog(
        user_id=operator.id,
        action="OPERATOR_COMPLETE_PRINT",
        target_type="print_job",
        target_id=job.id,
        details={"printer_id": job.printer_id, "collection_code": job.collection_code},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return job


@router.post("/jobs/{job_id}/fail")
async def fail_job(
    job_id: int,
    operator: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.user), selectinload(PrintJob.document))
        .where(PrintJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.retry_count += 1
    if job.retry_count <= 3:
        job.status = JobStatus.QUEUED
        job.priority_score -= 50
        await queue_service.enqueue(job.id, job.priority_score, {"retry": job.retry_count})
        await notify_job_status(db, job, job.user.email, "queued")
        message = "Job requeued for automatic reprint"
    else:
        job.status = JobStatus.FAILED
        await notify_job_status(db, job, job.user.email, "failed")
        message = "Job failed after max retries"

    if job.printer_id:
        printer_result = await db.execute(select(Printer).where(Printer.id == job.printer_id))
        printer = printer_result.scalar_one_or_none()
        if printer:
            printer.jobs_failed += 1
            printer.health_score = max(0, printer.health_score - 5)
            printer.status = PrinterStatus.ONLINE

    audit = AuditLog(
        user_id=operator.id,
        action="OPERATOR_FAIL_PRINT",
        target_type="print_job",
        target_id=job.id,
        details={"printer_id": job.printer_id, "retry_count": job.retry_count, "message": message},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"job_id": job.id, "status": job.status.value, "message": message}


@router.post("/process-queue")
async def process_next_in_queue(
    operator: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Dequeue highest priority job and assign a printer."""
    item = await queue_service.dequeue()
    if not item:
        return {"message": "Queue empty"}

    job_id, _ = item
    result = await db.execute(select(PrintJob).where(PrintJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return {"message": "Job not found in DB"}

    printer = await assign_printer(db, job)
    job.status = JobStatus.PRINTING

    audit = AuditLog(
        user_id=operator.id,
        action="OPERATOR_PROCESS_QUEUE",
        target_type="print_job",
        target_id=job.id,
        details={"printer_id": printer.id if printer else None, "printer_name": printer.name if printer else None},
    )
    db.add(audit)
    await invalidate_analytics_cache()

    return {"job_id": job.id, "printer": printer.name if printer else None, "status": "printing"}


@router.get("/printers", response_model=list[PrinterResponse])
async def list_printers(
    _: User = Depends(require_roles(UserRole.PRINT_CENTER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Printer).where(Printer.is_active == True))  # noqa: E712
    return result.scalars().all()

