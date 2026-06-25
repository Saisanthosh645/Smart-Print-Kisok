from datetime import datetime, timezone
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.printer import Printer, PrinterStatus
from app.models.print_job import PrintJob
from app.services.email_service import send_order_notification
from app.services.queue_service import queue_service


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.add(notif)
    return notif


async def publish_job_status_update(user_id: int, job_id: int, status: str, metadata: dict = None):
    channel = f"user_jobs_{user_id}"
    message = {
        "event": "job_status_update",
        "job_id": job_id,
        "status": status,
        **(metadata or {})
    }
    try:
        await queue_service.redis.publish(channel, json.dumps(message))
    except Exception:
        pass


async def notify_job_status(
    db: AsyncSession,
    job: PrintJob,
    user_email: str,
    new_status: str,
) -> None:
    history = list(job.status_history or [])
    history.append({"status": new_status, "at": datetime.now(timezone.utc).isoformat()})
    job.status_history = history

    titles = {
        "uploaded": "Order Received",
        "processing": "Processing Your Document",
        "queued": "Added to Print Queue",
        "printing": "Printing Started",
        "completed": "Print Job Completed",
        "failed": "Print Job Failed",
    }
    title = titles.get(new_status, f"Status: {new_status}")
    message = f"Your print job #{job.id} is now {new_status}."
    if new_status == "completed" and job.collection_code:
        message += f" Collection code: {job.collection_code}"

    await create_notification(db, job.user_id, title, message, f"job_{new_status}")
    await send_order_notification(user_email, job.id, new_status, job.collection_code)
    await publish_job_status_update(
        job.user_id,
        job.id,
        new_status,
        {
            "collection_code": job.collection_code,
            "kiosk_location": job.kiosk_location,
            "cost": job.cost,
            "message": message,
        }
    )


async def assign_printer(db: AsyncSession, job: PrintJob) -> Printer | None:
    query = select(Printer).where(
        Printer.is_active == True,  # noqa: E712
        Printer.status.in_([PrinterStatus.ONLINE, PrinterStatus.BUSY]),
    )
    if job.is_color:
        query = query.where(Printer.supports_color == True)  # noqa: E712
    if job.is_double_sided:
        query = query.where(Printer.supports_duplex == True)  # noqa: E712

    result = await db.execute(query.order_by(Printer.health_score.desc()))
    printers = result.scalars().all()
    if not printers:
        return None

    # Pick printer with best health and fewest active jobs
    best = min(printers, key=lambda p: (p.jobs_failed / max(p.jobs_completed, 1), -p.health_score))
    job.printer_id = best.id
    best.status = PrinterStatus.BUSY
    return best
