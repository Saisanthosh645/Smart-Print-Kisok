import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import select

from app.api import admin, auth, print_center, student, ws
from app.config import settings
from app.core.security import hash_password
from app.database import Base, async_session, engine
from app.models.printer import Printer
from app.models.user import User, UserRole
from app.services.queue_service import queue_service

logger = logging.getLogger(__name__)


async def seed_data() -> None:
    async with async_session() as db:
        admin_exists = await db.execute(select(User).where(User.email == "admin@smartprintx.com"))
        if not admin_exists.scalar_one_or_none():
            db.add(User(
                email="admin@smartprintx.com",
                full_name="System Admin",
                hashed_password=hash_password("admin12345"),
                role=UserRole.ADMIN,
                is_verified=True,
            ))
            db.add(User(
                email="operator@smartprintx.com",
                full_name="Print Center Operator",
                hashed_password=hash_password("operator123"),
                role=UserRole.PRINT_CENTER,
                is_verified=True,
            ))
            db.add(User(
                email="student@demo.com",
                full_name="Demo Student",
                hashed_password=hash_password("student123"),
                role=UserRole.STUDENT,
                is_verified=True,
            ))

        printer_exists = await db.execute(select(Printer).limit(1))
        if not printer_exists.scalar_one_or_none():
            db.add_all([
                Printer(name="Kiosk A1", location="Library Ground Floor", building="Central Library"),
                Printer(name="Kiosk B2", location="Engineering Block", building="Engineering"),
                Printer(name="Print Center Main", location="Admin Building Room 101", building="Admin"),
            ])
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await queue_service.connect()
    await seed_data()
    logger.info("SmartPrintX started")
    yield
    await queue_service.disconnect()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Campus Printing Ecosystem",
    version="1.0.0",
    lifespan=lifespan,
)

# Exception handling middleware
@app.middleware("http")
async def exception_handler_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        logger.exception(f"Unhandled exception occurred. Request ID: {request_id}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id
            }
        )

# HTTP Request Logging & Profiling middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    logger.info(f"[{request_id}] START {request.method} {request.url.path}")
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"[{request_id}] END {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.USE_LOCAL_STORAGE:
    upload_path = Path(settings.LOCAL_STORAGE_PATH)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(student.router, prefix="/api/v1")
app.include_router(print_center.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}
