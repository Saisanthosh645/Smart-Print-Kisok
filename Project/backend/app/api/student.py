import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.core.tokens import generate_collection_code
from app.database import get_db
from app.core.rate_limiter import RateLimiter
from app.core.pagination import paginate
from app.models.document import Document, FileType
from app.models.payment import Payment, PaymentRecordStatus
from app.models.print_job import JobStatus, PaymentStatus, PrintJob
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.audit_log import AuditLog
from app.schemas import (
    CostEstimateRequest,
    CostEstimateResponse,
    DocumentResponse,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PrintJobCreate,
    PrintJobResponse,
    RecommendationResponse,
    PaginatedDocuments,
    PaginatedPrintJobs,
)
from app.services.cost_calculator import estimate_print
from app.services.document_analyzer import analyze_document, count_pages
from app.services.notification_service import notify_job_status
from app.services.payment_service import payment_service
from app.services.queue_service import queue_service
from app.services.recommendation_service import get_cheapest_settings, get_fastest_collection, get_nearby_kiosks
from app.services.storage_service import storage_service

router = APIRouter(prefix="/student", tags=["student"])

ALLOWED_EXTENSIONS = {".pdf": FileType.PDF, ".docx": FileType.DOCX, ".pptx": FileType.PPTX}


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Supported formats: PDF, DOCX, PPTX")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    file_type = ALLOWED_EXTENSIONS[ext]
    page_count = count_pages(content, file_type)
    analysis = analyze_document(content, file_type)
    storage_key = await storage_service.upload(content, file.filename or "document", file.content_type or "application/octet-stream")

    doc = Document(
        user_id=user.id,
        filename=file.filename or "document",
        storage_key=storage_key,
        file_type=file_type,
        page_count=page_count,
        analysis=analysis,
    )
    db.add(doc)
    await db.flush()

    audit = AuditLog(
        user_id=user.id,
        action="DOCUMENT_UPLOAD",
        target_type="document",
        target_id=doc.id,
        details={"filename": doc.filename, "page_count": doc.page_count},
    )
    db.add(audit)

    return doc


@router.get("/documents", response_model=PaginatedDocuments)
async def list_documents(
    page: int = 1,
    size: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    return await paginate(db, query, page, size)


@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_cost(
    data: CostEstimateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == data.document_id, Document.user_id == user.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages, sheets, cost, breakdown, suggestions = estimate_print(
        doc.page_count, data.options.page_range, data.options.is_color, data.options.is_double_sided
    )
    return CostEstimateResponse(
        pages_to_print=pages,
        sheets_required=sheets,
        cost=cost,
        breakdown=breakdown,
        optimization_suggestions=suggestions,
    )


@router.post(
    "/jobs",
    response_model=PrintJobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def create_print_job(
    data: PrintJobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == data.document_id, Document.user_id == user.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages, sheets, cost, _, _ = estimate_print(
        doc.page_count, data.options.page_range, data.options.is_color, data.options.is_double_sided
    )

    job = PrintJob(
        user_id=user.id,
        document_id=doc.id,
        is_color=data.options.is_color,
        is_double_sided=data.options.is_double_sided,
        page_range=data.options.page_range,
        pages_to_print=pages,
        sheets_required=sheets,
        cost=cost,
        is_urgent=data.options.is_urgent,
        kiosk_location=data.options.kiosk_location,
        status=JobStatus.UPLOADED,
        status_history=[{"status": "uploaded", "at": time.time()}],
    )
    job.priority_score = queue_service.compute_priority(
        0, time.time(), data.options.is_urgent, user.is_premium
    )
    db.add(job)
    await db.flush()
    job.priority_score = queue_service.compute_priority(
        job.id, job.created_at.timestamp(), data.options.is_urgent, user.is_premium
    )

    audit = AuditLog(
        user_id=user.id,
        action="JOB_CREATE",
        target_type="print_job",
        target_id=job.id,
        details={"cost": job.cost, "pages": job.pages_to_print},
    )
    db.add(audit)

    await notify_job_status(db, job, user.email, "uploaded")
    # Invalidate cache
    from app.services.analytics_service import invalidate_analytics_cache
    await invalidate_analytics_cache()

    job_res = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.document), selectinload(PrintJob.printer))
        .where(PrintJob.id == job.id)
    )
    return job_res.scalar_one()


@router.get("/jobs", response_model=PaginatedPrintJobs)
async def list_jobs(
    page: int = 1,
    size: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(PrintJob)
        .options(selectinload(PrintJob.document), selectinload(PrintJob.printer))
        .where(PrintJob.user_id == user.id)
        .order_by(PrintJob.created_at.desc())
    )
    return await paginate(db, query, page, size)


@router.get("/jobs/{job_id}", response_model=PrintJobResponse)
async def get_job(
    job_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.document), selectinload(PrintJob.printer))
        .where(PrintJob.id == job_id, PrintJob.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post(
    "/jobs/{job_id}/pay",
    response_model=PaymentOrderResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def create_payment(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PrintJob).where(PrintJob.id == job_id, PrintJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Already paid")

    order = await payment_service.create_order(job.cost, job.id)
    payment = Payment(print_job_id=job.id, razorpay_order_id=order["id"], amount=job.cost)
    db.add(payment)
    return PaymentOrderResponse(
        order_id=order["id"],
        amount=job.cost,
        currency=order["currency"],
        key_id=order["key_id"],
        mock=order.get("mock", False),
    )


@router.post(
    "/jobs/{job_id}/verify-payment",
    response_model=PrintJobResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def verify_payment(
    job_id: int,
    data: PaymentVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.document), selectinload(PrintJob.printer))
        .where(PrintJob.id == job_id, PrintJob.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not payment_service.verify_signature(
        data.razorpay_order_id, data.razorpay_payment_id, data.razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    pay_result = await db.execute(select(Payment).where(Payment.print_job_id == job.id))
    payment = pay_result.scalar_one_or_none()
    if payment:
        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.status = PaymentRecordStatus.PAID
        payment.method = data.method

    job.payment_status = PaymentStatus.PAID
    job.status = JobStatus.PROCESSING
    await notify_job_status(db, job, user.email, "processing")

    # Add ledger transaction
    transaction = Transaction(
        user_id=user.id,
        payment_id=payment.id if payment else None,
        amount=job.cost,
        transaction_type=TransactionType.CHARGE,
        description=f"Print Job #{job.id} Charge",
    )
    db.add(transaction)

    # Add Audit Log
    audit = AuditLog(
        user_id=user.id,
        action="PAYMENT_VERIFIED",
        target_type="print_job",
        target_id=job.id,
        details={"payment_id": payment.id if payment else None, "amount": job.cost},
    )
    db.add(audit)

    job.status = JobStatus.QUEUED
    await notify_job_status(db, job, user.email, "queued")
    await queue_service.enqueue(job.id, job.priority_score, {"user_id": user.id, "cost": job.cost})

    # Trigger Celery worker task asynchronously
    from app.tasks.print_tasks import process_print_job
    process_print_job.delay(job.id)

    # Invalidate cache
    from app.services.analytics_service import invalidate_analytics_cache
    await invalidate_analytics_cache()

    return job


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    document_id: int | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page_count = 10
    if document_id:
        result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == user.id))
        doc = result.scalar_one_or_none()
        if doc:
            page_count = doc.page_count

    cheapest = await get_cheapest_settings(db, document_id or 0, page_count)
    kiosks = await get_nearby_kiosks(db)
    fastest = await get_fastest_collection(db)
    return RecommendationResponse(
        cheapest_settings=cheapest,
        nearby_kiosks=kiosks,
        fastest_collection=fastest,
    )


@router.get("/notifications")
async def get_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.notification import Notification

    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)
    )
    return result.scalars().all()
