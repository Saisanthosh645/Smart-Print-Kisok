import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PrinterStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    building: Mapped[str] = mapped_column(String(255), default="Main Campus")
    supports_color: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_duplex: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[PrinterStatus] = mapped_column(Enum(PrinterStatus), default=PrinterStatus.ONLINE, index=True)
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("PrintJob", back_populates="printer")
