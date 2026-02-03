from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from accounts.models import SavedAddress
from store.models import ProductImage, Product

# ==========================================
# 1. CART SERIALIZERS
# ==========================================

class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='variant.product.title')
    product_slug = serializers.ReadOnlyField(source='variant.product.slug')
    size = serializers.ReadOnlyField(source='variant.size.name') 
    price = serializers.DecimalField(source='price_per_unit', max_digits=10, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(source='total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product_title', 'product_slug', 'size', 'variant', 'quantity', 'price', 'subtotal', 'image')

    def get_image(self, obj):
        # Fetch the first image for the product
        image = ProductImage.objects.filter(product=obj.variant.product).first()
        if image and image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
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
    product_slug = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    exchange_coupon_code = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product_name", "product_slug", "variant_label", "price", "quantity", "image", "status", "exchange_coupon_code","admin_comment")

    def get_product_slug(self, obj):
        # Safely try to find product, fallback to name slug
        product = Product.objects.filter(title__iexact=obj.product_name).first()
        if product:
            return product.slug
        return obj.product_name.lower().replace(" ", "-")

    def get_image(self, obj):
        # 1. Find the product
        product = Product.objects.filter(title__iexact=obj.product_name).first()
        
        if product:
            # 2. Get the first image (Removed invalid order_by('-is_primary'))
            image_obj = ProductImage.objects.filter(product=product).first()
            
            if image_obj and image_obj.image:
                try:
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(image_obj.image.url)
                    return image_obj.image.url
                except:
                    return image_obj.image.url
        return None

    def get_exchange_coupon_code(self, obj):
        if obj.exchange_coupon:
            return obj.exchange_coupon.code
        return None

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id", "total_amount", "payment_status", "order_status",
            "razorpay_order_id", "razorpay_payment_id", "razorpay_refund_id",
            "created_at", "date", "shipping_address", "phone", "items","tracking_link"
        )
        read_only_fields = ('user', 'payment_status', 'order_status', 'razorpay_order_id')

    def get_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y")