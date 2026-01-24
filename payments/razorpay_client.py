import decimal
import logging
import razorpay
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_client() -> razorpay.Client:
    key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None)
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay credentials missing.")
    return razorpay.Client(auth=(key_id, key_secret))

def create_order(amount, currency: str = "INR") -> dict:
    if isinstance(amount, decimal.Decimal):
        amount = float(amount)
    amount_paise = int(round(amount * 100))
    client = _get_client()
    return client.order.create({"amount": amount_paise, "currency": currency})

def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    client = _get_client()
    client.utility.verify_payment_signature({
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    })
    return True

# ✅ NEW: Handle Refunds
def refund_payment(payment_id: str, amount: float, notes: dict = None) -> dict:
    """
    Refunds a payment via Razorpay.
    Amount should be in Rupees (converted to paise internally).
    """
    client = _get_client()
    amount_paise = int(round(amount * 100))
    return client.payment.refund(payment_id, amount_paise, {"notes": notes or {}})