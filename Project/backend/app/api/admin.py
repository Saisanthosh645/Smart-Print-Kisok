from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.database import get_db
from app.core.pagination import paginate
from app.models.payment import Payment, PaymentRecordStatus
from app.models.print_job import PaymentStatus, PrintJob
from app.models.printer import Printer
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType
from app.models.audit_log import AuditLog
from app.schemas import (
    AnalyticsResponse,
    BanUserRequest,
    PrinterCreate,
    PrinterResponse,
    RefundRequest,
    UserResponse,
    PaginatedUsers,
)
from app.services.analytics_service import get_analytics, invalidate_analytics_cache

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics", response_model=AnalyticsResponse)
async def analytics(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await get_analytics(db)


@router.get("/users", response_model=PaginatedUsers)
async def list_users(
    page: int = 1,
    size: int = 20,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(User.created_at.desc())
    return await paginate(db, query, page, size)


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    data: BanUserRequest,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = True

    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_BAN",
        target_type="user",
        target_id=user.id,
        details={"reason": data.reason},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"message": f"User banned: {data.reason}"}


@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False

    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_UNBAN",
        target_type="user",
        target_id=user.id,
        details={},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"message": "User unbanned"}


@router.post("/users/{user_id}/premium")
async def toggle_premium(
    user_id: int,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_premium = not user.is_premium

    audit = AuditLog(
        user_id=admin_user.id,
        action="USER_PREMIUM_TOGGLE",
        target_type="user",
        target_id=user.id,
        details={"is_premium": user.is_premium},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"is_premium": user.is_premium}


@router.post("/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: int,
    data: RefundRequest,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = PaymentRecordStatus.REFUNDED
    job_result = await db.execute(select(PrintJob).where(PrintJob.id == payment.print_job_id))
    job = job_result.scalar_one_or_none()
    if job:
        job.payment_status = PaymentStatus.REFUNDED

    # Log financial refund ledger transaction
    transaction = Transaction(
        user_id=job.user_id if job else admin_user.id,
        payment_id=payment.id,
        amount=-payment.amount,  # negative for refund
        transaction_type=TransactionType.REFUND,
        description=f"Refund for payment {payment.id} - Reason: {data.reason}",
    )
    db.add(transaction)

    audit = AuditLog(
        user_id=admin_user.id,
        action="PAYMENT_REFUND",
        target_type="payment",
        target_id=payment.id,
        details={"reason": data.reason, "amount": payment.amount},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"message": f"Refund processed: {data.reason}"}


@router.get("/printers", response_model=list[PrinterResponse])
async def admin_list_printers(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Printer))
    return result.scalars().all()


@router.post("/printers", response_model=PrinterResponse, status_code=201)
async def add_printer(
    data: PrinterCreate,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    printer = Printer(**data.model_dump())
    db.add(printer)
    await db.flush()

    audit = AuditLog(
        user_id=admin_user.id,
        action="PRINTER_ADD",
        target_type="printer",
        target_id=printer.id,
        details={"name": printer.name, "location": printer.location},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return printer


@router.patch("/printers/{printer_id}/health")
async def update_printer_health(
    printer_id: int,
    health_score: float,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer.health_score = max(0, min(100, health_score))

    audit = AuditLog(
        user_id=admin_user.id,
        action="PRINTER_HEALTH_UPDATE",
        target_type="printer",
        target_id=printer.id,
        details={"health_score": printer.health_score},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"printer_id": printer.id, "health_score": printer.health_score}


@router.delete("/printers/{printer_id}")
async def deactivate_printer(
    printer_id: int,
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer.is_active = False

    audit = AuditLog(
        user_id=admin_user.id,
        action="PRINTER_DEACTIVATE",
        target_type="printer",
        target_id=printer.id,
        details={},
    )
    db.add(audit)
    await invalidate_analytics_cache()
    return {"message": "Printer deactivated"}
