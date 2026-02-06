from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import OrderItem
from store.models import Coupon

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .whatsapp_utils import send_whatsapp_message


@receiver(pre_save, sender=OrderItem)
def handle_item_exchange(sender, instance, **kwargs):
    # Logic: If item is Approved AND has no coupon yet, generate one.
    if instance.status == 'Exchange Approved' and not instance.exchange_coupon:
        
        # 1. Generate Unique Code (e.g., EXCH-8829-ABX)
        code = f"EXCH-{instance.id}-{get_random_string(4).upper()}"
        
        # 2. Calculate Refund Value (Price * Quantity)
        refund_amount = instance.price * instance.quantity

        # 3. Create Coupon
        coupon = Coupon.objects.create(
            code=code,
            discount_type='fixed', # Ensure 'fixed' matches your Coupon model choices
            value=refund_amount,
            valid_from=timezone.now(),
            valid_to=timezone.now() + timezone.timedelta(days=90), # 3 Months Expiry
            active=True,
            usage_limit=1 # One-time use
        )

        # 4. Attach to Item
        instance.exchange_coupon = coupon
        print(f"✅ Generated Coupon {code} for Item #{instance.id}")


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem
from .whatsapp_utils import send_whatsapp_message

# --- 1. ORDER STATUS ALERTS ---
@receiver(post_save, sender=Order)
def order_status_notification(sender, instance, created, **kwargs):
    # Basic data
    customer_name = instance.user.first_name if instance.user.first_name else "Customer"
    phone = instance.phone
    order_id = str(instance.id)
    
    if not phone: return

    # A. New Order
    if created:
        if instance.payment_method == 'COD':
            msg = f"Hi {customer_name}, Thank you for your order {order_id}! Amount to pay on delivery: ₹{instance.total_amount}. We'll notify you when it ships."
        else:
            msg = f"Hi {customer_name}, Thank you for your order {order_id}! We have received your payment of ₹{instance.total_amount}. We'll notify you when it ships."
        
        send_whatsapp_message(phone, msg)

    # B. Status Changes
    else:
        if instance.order_status == 'Shipped':
            link = instance.tracking_link if instance.tracking_link else "Check app for details"
            msg = f"Hi {customer_name}, Great news! Your order {order_id} has been shipped. Track it here: {link}"
            send_whatsapp_message(phone, msg)

        elif instance.order_status == 'Delivered':
            msg = f"Hi {customer_name}, Order {order_id} is delivered! We hope you love your purchase."
            send_whatsapp_message(phone, msg)

        elif instance.order_status == 'Cancelled':
            if instance.payment_method == 'COD':
                msg = f"Hi {customer_name}, Order {order_id} has been cancelled as requested. No charges were applied."
            else:
                msg = f"Hi {customer_name}, Order {order_id} has been cancelled. Since you paid online, your refund of ₹{instance.total_amount} will be processed within 5-7 business days."
            
            send_whatsapp_message(phone, msg)

# --- 2. RETURN/EXCHANGE ALERTS ---
@receiver(post_save, sender=OrderItem)
def item_status_notification(sender, instance, created, **kwargs):
    if created: return

    order = instance.order
    phone = order.phone
    product = instance.product_name
    
    if not phone: return

    if instance.status == 'Return Approved':
        msg = f"Return Approved: Our courier partner will pick up '{product}' shortly."
        send_whatsapp_message(phone, msg)

    elif instance.status == 'Exchange Approved':
        code = instance.exchange_coupon.code if instance.exchange_coupon else "CONTACT-SUPPORT"
        msg = f"Exchange Approved for '{product}'. Use this coupon for your free replacement: {code}"
        send_whatsapp_message(phone, msg)