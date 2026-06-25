import heapq
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

QUEUE_KEY = "smartprintx:priority_queue"
JOB_DATA_PREFIX = "smartprintx:job:"


@dataclass(order=True)
class QueueItem:
    priority: float
    job_id: int = field(compare=False)
    enqueued_at: float = field(compare=False, default_factory=time.time)


class PriorityQueueService:
    """Redis-backed min-heap priority queue for print jobs."""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()

    @property
    def redis(self) -> redis.Redis:
        if not self._redis:
            raise RuntimeError("Redis not connected")
        return self._redis

    def compute_priority(
        self,
        job_id: int,
        created_at_ts: float,
        is_urgent: bool,
        is_premium: bool,
    ) -> float:
        """
        Lower score = higher priority (min-heap).
        Urgent and premium jobs get lower scores.
        """
        age_hours = max(0, (time.time() - created_at_ts) / 3600)
        score = -age_hours * 10 + job_id * 0.001
        if is_urgent:
            score -= 500
        if is_premium:
            score -= settings.PREMIUM_PRIORITY_BOOST
        return score

    async def enqueue(self, job_id: int, priority: float, metadata: dict[str, Any]) -> None:
        item = QueueItem(priority=-priority, job_id=job_id)
        await self.redis.zadd(QUEUE_KEY, {str(job_id): item.priority})
        await self.redis.set(f"{JOB_DATA_PREFIX}{job_id}", json.dumps(metadata), ex=86400 * 7)

    async def dequeue(self) -> tuple[int, dict[str, Any]] | None:
        result = await self.redis.zpopmin(QUEUE_KEY, count=1)
        if not result:
            return None
        job_id_str, _ = result[0]
        job_id = int(job_id_str)
        data = await self.redis.get(f"{JOB_DATA_PREFIX}{job_id}")
        metadata = json.loads(data) if data else {}
        return job_id, metadata

    async def peek_all(self, limit: int = 50) -> list[tuple[int, float]]:
        items = await self.redis.zrange(QUEUE_KEY, 0, limit - 1, withscores=True)
        return [(int(jid), -score) for jid, score in items]

    async def remove(self, job_id: int) -> None:
        await self.redis.zrem(QUEUE_KEY, str(job_id))
        await self.redis.delete(f"{JOB_DATA_PREFIX}{job_id}")

    async def size(self) -> int:
        return await self.redis.zcard(QUEUE_KEY)

    async def rebuild_heap_from_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Rebuild queue from DB jobs using heap logic."""
        await self.redis.delete(QUEUE_KEY)
        heap: list[QueueItem] = []
        for job in jobs:
            item = QueueItem(priority=-job["priority_score"], job_id=job["id"])
            heapq.heappush(heap, item)
            await self.redis.set(f"{JOB_DATA_PREFIX}{job['id']}", json.dumps(job), ex=86400 * 7)

        for item in heap:
            await self.redis.zadd(QUEUE_KEY, {str(item.job_id): item.priority})


queue_service = PriorityQueueService()
