import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.queue_service import queue_service

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def broadcast_to_user(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.debug(f"Failed to send websocket message: {e}")


manager = ConnectionManager()


@router.websocket("/jobs")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    from app.core.security import decode_token

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
    except Exception as e:
        logger.warning(f"WebSocket connection rejected due to invalid token: {e}")
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)

    pubsub = queue_service.redis.pubsub()
    channel = f"user_jobs_{user_id}"
    await pubsub.subscribe(channel)

    async def listen_redis():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in Redis PubSub WS listener for user {user_id}: {e}")
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass

    redis_task = asyncio.create_task(listen_redis())

    try:
        while True:
            # Maintain connection, listen for any messages (or pings) from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    finally:
        redis_task.cancel()
        try:
            await redis_task
        except Exception:
            pass
