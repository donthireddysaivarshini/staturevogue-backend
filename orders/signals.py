from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import OrderItem
from store.models import Coupon




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

