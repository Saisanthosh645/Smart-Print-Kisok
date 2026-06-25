import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"


class PaymentRecordStatus(str, enum.Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    print_job_id: Mapped[int] = mapped_column(ForeignKey("print_jobs.id"), unique=True, index=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod), nullable=True)
    status: Mapped[PaymentRecordStatus] = mapped_column(Enum(PaymentRecordStatus), default=PaymentRecordStatus.CREATED, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    print_job = relationship("PrintJob", back_populates="payment")
