from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models.document import FileType
from app.models.payment import PaymentMethod, PaymentRecordStatus
from app.models.print_job import JobStatus, PaymentStatus
from app.models.printer import PrinterStatus
from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_verified: bool
    is_premium: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class PrintOptions(BaseModel):
    is_color: bool = False
    is_double_sided: bool = False
    page_range: str | None = None
    is_urgent: bool = False
    kiosk_location: str | None = None


class CostEstimateRequest(BaseModel):
    document_id: int
    options: PrintOptions


class CostEstimateResponse(BaseModel):
    pages_to_print: int
    sheets_required: int
    cost: float
    breakdown: dict[str, Any]
    optimization_suggestions: list[str]


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: FileType
    page_count: int
    analysis: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PrintJobCreate(BaseModel):
    document_id: int
    options: PrintOptions


class PrintJobResponse(BaseModel):
    id: int
    status: JobStatus
    payment_status: PaymentStatus
    is_color: bool
    is_double_sided: bool
    page_range: str | None
    pages_to_print: int
    sheets_required: int
    cost: float
    priority_score: float
    collection_code: str | None
    kiosk_location: str | None
    status_history: list | None
    document: DocumentResponse | None = None
    printer_id: int | None = None
    printer: PrinterResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    key_id: str
    mock: bool = False


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    method: PaymentMethod = PaymentMethod.UPI


class PaymentResponse(BaseModel):
    id: int
    print_job_id: int
    amount: float
    status: PaymentRecordStatus
    method: PaymentMethod | None

    model_config = {"from_attributes": True}


class PrinterCreate(BaseModel):
    name: str
    location: str
    building: str = "Main Campus"
    supports_color: bool = True
    supports_duplex: bool = True


class PrinterResponse(BaseModel):
    id: int
    name: str
    location: str
    building: str
    supports_color: bool
    supports_duplex: bool
    status: PrinterStatus
    health_score: float
    jobs_completed: int
    jobs_failed: int
    is_active: bool

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsResponse(BaseModel):
    daily_revenue: float
    monthly_revenue: float
    total_prints: int
    active_users: int
    jobs_by_status: dict[str, int]
    revenue_by_day: list[dict[str, Any]]


class RecommendationResponse(BaseModel):
    cheapest_settings: dict[str, Any]
    nearby_kiosks: list[dict[str, Any]]
    fastest_collection: dict[str, Any] | None


class BanUserRequest(BaseModel):
    reason: str = "Policy violation"


class RefundRequest(BaseModel):
    reason: str = "Customer request"


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    payment_id: int | None
    amount: float
    transaction_type: str  # charge, refund
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    target_type: str | None
    target_id: int | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Paginated responses
class PageMetadataSchema(BaseModel):
    total: int
    page: int
    size: int
    pages: int


class PaginatedPrintJobs(BaseModel):
    items: list[PrintJobResponse]
    metadata: PageMetadataSchema


class PaginatedDocuments(BaseModel):
    items: list[DocumentResponse]
    metadata: PageMetadataSchema


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    metadata: PageMetadataSchema

