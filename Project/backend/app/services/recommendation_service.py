from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.printer import Printer, PrinterStatus
from app.models.print_job import JobStatus, PrintJob
from app.services.cost_calculator import calculate_cost, calculate_sheets


async def get_cheapest_settings(db: AsyncSession, document_id: int, page_count: int) -> dict:
    options = []
    for color in (False, True):
        for duplex in (False, True):
            cost, breakdown = calculate_cost(page_count, color, duplex)
            options.append({"is_color": color, "is_double_sided": duplex, "cost": cost, **breakdown})

    cheapest = min(options, key=lambda o: o["cost"])
    return {
        "recommended": cheapest,
        "all_options": sorted(options, key=lambda o: o["cost"]),
        "savings_vs_worst": round(max(o["cost"] for o in options) - cheapest["cost"], 2),
    }


async def get_nearby_kiosks(db: AsyncSession, user_location: str | None = None) -> list[dict]:
    result = await db.execute(
        select(Printer).where(Printer.is_active == True).order_by(Printer.health_score.desc())  # noqa: E712
    )
    printers = result.scalars().all()

    kiosks = []
    for p in printers:
        queue_size = await _queue_size_at_printer(db, p.id)
        kiosks.append({
            "printer_id": p.id,
            "name": p.name,
            "location": p.location,
            "building": p.building,
            "status": p.status.value,
            "health_score": p.health_score,
            "queue_size": queue_size,
            "estimated_wait_minutes": queue_size * 3,
        })

    kiosks.sort(key=lambda k: (k["queue_size"], -k["health_score"]))
    return kiosks


async def get_fastest_collection(db: AsyncSession) -> dict | None:
    kiosks = await get_nearby_kiosks(db)
    online = [k for k in kiosks if k["status"] in ("online", "busy")]
    return online[0] if online else None


async def _queue_size_at_printer(db: AsyncSession, printer_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(PrintJob)
        .where(
            PrintJob.printer_id == printer_id,
            PrintJob.status.in_([JobStatus.QUEUED, JobStatus.PRINTING]),
        )
    )
    return result.scalar() or 0
