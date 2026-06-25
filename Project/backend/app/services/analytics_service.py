from datetime import datetime, timedelta, timezone
import json
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentRecordStatus
from app.models.print_job import JobStatus, PaymentStatus, PrintJob
from app.models.user import User
from app.services.queue_service import queue_service

ANALYTICS_CACHE_KEY = "cache:admin_analytics"
logger = logging.getLogger(__name__)


async def invalidate_analytics_cache() -> None:
    try:
        redis_client = queue_service.redis
        await redis_client.delete(ANALYTICS_CACHE_KEY)
        logger.info("Admin analytics cache invalidated.")
    except Exception as e:
        logger.error(f"Redis cache invalidate error: {e}")


async def get_analytics(db: AsyncSession) -> dict:
    try:
        redis_client = queue_service.redis
        cached = await redis_client.get(ANALYTICS_CACHE_KEY)
        if cached:
            logger.info("Serving admin analytics from Redis cache.")
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Redis cache read error: {e}")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    daily_revenue = await _sum_revenue(db, since=today_start)
    monthly_revenue = await _sum_revenue(db, since=month_start)

    total_prints = await db.scalar(
        select(func.count()).select_from(PrintJob).where(PrintJob.status == JobStatus.COMPLETED)
    )

    active_users = await db.scalar(
        select(func.count(func.distinct(PrintJob.user_id)))
        .select_from(PrintJob)
        .where(PrintJob.created_at >= month_start)
    )

    status_counts = {}
    for status in JobStatus:
        count = await db.scalar(
            select(func.count()).select_from(PrintJob).where(PrintJob.status == status)
        )
        status_counts[status.value] = count or 0

    revenue_by_day = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        rev = await _sum_revenue(db, since=day, until=next_day)
        revenue_by_day.append({"date": day.strftime("%Y-%m-%d"), "revenue": rev})

    data = {
        "daily_revenue": daily_revenue,
        "monthly_revenue": monthly_revenue,
        "total_prints": total_prints or 0,
        "active_users": active_users or 0,
        "jobs_by_status": status_counts,
        "revenue_by_day": revenue_by_day,
    }

    try:
        redis_client = queue_service.redis
        await redis_client.set(ANALYTICS_CACHE_KEY, json.dumps(data), ex=60)
        logger.info("Admin analytics cache stored in Redis.")
    except Exception as e:
        logger.error(f"Redis cache write error: {e}")

    return data


async def _sum_revenue(db: AsyncSession, since: datetime, until: datetime | None = None) -> float:
    query = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .select_from(Payment)
        .where(Payment.status == PaymentRecordStatus.PAID, Payment.created_at >= since)
    )
    if until:
        query = query.where(Payment.created_at < until)
    result = await db.scalar(query)
    return float(result or 0)

