from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from accounts.models import SavedAddress
from store.models import ProductImage

# ==========================================
# 1. CART SERIALIZERS
# ==========================================

class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='variant.product.title')
    product_slug = serializers.ReadOnlyField(source='variant.product.slug')
    size = serializers.ReadOnlyField(source='variant.size')
    price = serializers.DecimalField(source='price_per_unit', max_digits=10, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(source='total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product_title', 'product_slug', 'size', 'variant', 'quantity', 'price', 'subtotal', 'image')

    def get_image(self, obj):
        # Fetch the primary image for the product
        image = ProductImage.objects.filter(product=obj.variant.product, is_primary=True).first()
        if image:
            return image.image.url
        return None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_cart_price = serializers.DecimalField(source='total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items', 'total_cart_price', 'updated_at')

# ==========================================
# 2. ADDRESS SERIALIZERS
# ==========================================

class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = ('id', 'label', 'first_name', 'last_name', 'address', 'apartment', 'city', 'state', 'zip_code', 'country', 'phone', 'is_default')
        read_only_fields = ('id',)

# ==========================================
# 3. ORDER SERIALIZERS
# ==========================================

class OrderItemSerializer(serializers.ModelSerializer):
    # Frontend expects specific field names for the Order History page
    product_slug = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product_name", "product_slug", "variant_label", "price", "quantity")

    def get_product_slug(self, obj):
        # Generate a slug from the name if not stored directly, 
        # or fetch from product relation if you added it to the model.
        # For now, simple slugify of the name:
        return obj.product_name.lower().replace(" ", "-")

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    date = serializers.SerializerMethodField() # For "Placed on Jan 25, 2026"

    class Meta:
        model = Order
        fields = (
            "id",
            "total_amount",
            "payment_status",
            "order_status",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_refund_id", # 
            "created_at",
            "date",
            "shipping_address",
            "phone",
            "items",
        )
        read_only_fields = ('user', 'payment_status', 'order_status', 'razorpay_order_id')

    def get_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y")