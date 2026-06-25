import hashlib
import hmac
import logging
import uuid

from app.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self) -> None:
        self.mock = settings.RAZORPAY_MOCK or not settings.RAZORPAY_KEY_ID
        self.client = None
        if not self.mock:
            try:
                import razorpay
            except ImportError as exc:
                raise RuntimeError(
                    "Razorpay SDK is required when Razorpay is enabled. "
                    "Install razorpay or enable RAZORPAY_MOCK."
                ) from exc

            self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    async def create_order(self, amount: float, job_id: int) -> dict:
        amount_paise = int(amount * 100)
        if self.mock:
            order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
            logger.info("Mock Razorpay order: %s amount=%s job=%s", order_id, amount, job_id)
            return {
                "id": order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": "rzp_mock_key",
                "mock": True,
            }

        order = self.client.order.create(
            {"amount": amount_paise, "currency": "INR", "receipt": f"job_{job_id}"}
        )
        return {
            "id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "mock": False,
        }

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if self.mock:
            return signature == "mock_signature_valid"

        payload = f"{order_id}|{payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


payment_service = PaymentService()
