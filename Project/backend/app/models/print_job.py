import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    QUEUED = "queued"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    printer_id: Mapped[int | None] = mapped_column(ForeignKey("printers.id"), nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.UPLOADED, index=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    is_color: Mapped[bool] = mapped_column(Boolean, default=False)
    is_double_sided: Mapped[bool] = mapped_column(Boolean, default=False)
    page_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pages_to_print: Mapped[int] = mapped_column(Integer, default=0)
    sheets_required: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    collection_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    kiosk_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_history: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="print_jobs")
    document = relationship("Document", back_populates="print_jobs")
    printer = relationship("Printer", back_populates="jobs")
    payment = relationship("Payment", back_populates="print_job", uselist=False)
