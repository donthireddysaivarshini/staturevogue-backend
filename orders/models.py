from django.db import models
from django.conf import settings
from store.models import ProductVariant

# --- CART MODELS ---
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def price_per_unit(self):
        return self.variant.product.price + self.variant.additional_price
    
    @property
    def total_price(self):
        return self.price_per_unit * self.quantity

# --- ORDER MODELS ---
class Order(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Refunded', 'Refunded'), # ✅ Added
    )
    
    ORDER_STATUS_CHOICES = (
        # Standard Flow
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'), # ✅ Added
        
        # Return Flow
        ('Return Requested', 'Return Requested'), # ✅ Added
        ('Return Approved', 'Return Approved'),
        ('Returned', 'Returned'),
        ('Refund Initiated', 'Refund Initiated'),
        
        # Exchange Flow
        ('Exchange Requested', 'Exchange Requested'), # ✅ Added
        ('Exchange Approved', 'Exchange Approved'),
        ('Exchange Shipped', 'Exchange Shipped'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    # Shipping Info
    shipping_address = models.TextField()
    phone = models.CharField(max_length=20)
    
    # Payment Info
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='Processing')
    
    # Razorpay Integration Fields
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # ✅ New: Refund Tracking
    razorpay_refund_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.order_status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    variant_label = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"