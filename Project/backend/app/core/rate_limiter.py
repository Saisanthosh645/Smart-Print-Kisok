import logging
from fastapi import HTTPException, Request, status

from app.services.queue_service import queue_service

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        try:
            redis_client = queue_service.redis
        except RuntimeError:
            # Fallback if Redis is not initialized or in a non-connected test env
            return

        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization")
        identifier = f"ip:{client_ip}"

        if auth_header and auth_header.startswith("Bearer "):
            from app.core.security import decode_token

            try:
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                sub = payload.get("sub")
                if sub:
                    identifier = f"user:{sub}"
            except Exception:
                pass

        path = request.url.path
        key = f"rate_limit:{path}:{identifier}"

        current = await redis_client.get(key)
        if current and int(current) >= self.times:
            ttl = await redis_client.ttl(key)
            wait_time = ttl if ttl > 0 else self.seconds
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {wait_time} seconds.",
            )

        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, self.seconds)
            await pipe.execute()
