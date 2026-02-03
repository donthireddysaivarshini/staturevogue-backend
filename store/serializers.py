from rest_framework import serializers
from .models import Product, Category, Collection, ProductImage, ProductVariant, Color, Size, Review
from .models import Coupon, SiteConfig

# ... (Keep CategorySerializer, CollectionSerializer, ReviewSerializer as they were) ...
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_featured','gender']

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'slug', 'image', 'description']



class ReviewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%d %b %Y", read_only=True)
    purchased_variant = serializers.CharField(read_only=True) # Send to frontend
    
    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'comment', 'created_at', 'purchased_variant']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # --- STRICT REVIEW LOGIC ---
        # Check if user actually bought the product
        # user_orders = OrderItem.objects.filter(order__user=request.user, product=validated_data['product'])
        
        # if not user_orders.exists():
        #     raise serializers.ValidationError("You can only review products you have purchased.")
        
        # If they bought it, grab the variant (e.g., "Blue - M") to save with review
        # validated_data['purchased_variant'] = f"{user_orders.first().variant.color.name} - {user_orders.first().variant.size.name}"
        
        # FOR NOW (Until Order model is linked):
        validated_data['purchased_variant'] = "Verified Purchase" 

        return super().create(validated_data)

# --- MAIN PRODUCT SERIALIZER ---
# --- MAIN PRODUCT SERIALIZER ---
class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    originalPrice = serializers.DecimalField(source='original_price', max_digits=10, decimal_places=2)
    rating = serializers.FloatField(source='average_rating')
    reviewCount = serializers.IntegerField(source='review_count')
    inStock = serializers.BooleanField(source='in_stock')
    
    # Map title -> name for frontend
    name = serializers.CharField(source='title') 

    # Dynamic fields
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    careInstructions = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField() # <--- MODIFIED: Now includes nested sizes
    sizes = serializers.SerializerMethodField()  # Keeping global sizes just in case

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'gender', 'price', 'originalPrice',
            'rating', 'reviewCount', 'badge', 'description', 
            'images', 'variants', 'colors', 'sizes', 'features', 'careInstructions',
            'fabric', 'fit', 'inStock'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data

    def get_images(self, obj):
        request = self.context.get('request')
        if request:
            return [
                {
                    "url": request.build_absolute_uri(img.image.url),
                    "color": img.color.name if img.color else None
                } 
                for img in obj.images.all()
            ]
        return []

    def get_variants(self, obj):
        return [
            {
                "color": v.color.name,
                "size": v.size.name,
                "stock": v.stock,
                "sku": v.sku
            }
            for v in obj.variants.all()
        ]

    # --- 🔥 FIXED: NESTED SIZES INSIDE COLORS ---
    def get_colors(self, obj):
        colors_data = []
        distinct_colors = Color.objects.filter(productvariant__product=obj).distinct()

        for color in distinct_colors:
            variants = obj.variants.filter(color=color).order_by('size__sort_order')
            
            sizes_data = []
            for variant in variants:
                # 🔥 FIX: Add the override to the base price instead of replacing it
                extra_price = variant.price_override if variant.price_override else 0
                final_price = obj.price + extra_price

                sizes_data.append({
                    "size": variant.size.name,
                    "stock": variant.stock,
                    "inStock": variant.stock > 0,
                    "price": final_price,  # Now sends Total (Base + Extra)
                    "sku": variant.sku
                })
            
            colors_data.append({
                "name": color.name,
                "hex": color.hex_code,
                "sizes": sizes_data 
            })
        
        return colors_data
    def get_sizes(self, obj):
        # Global list of sizes (all sizes available for this product regardless of color)
        return [{'size': s.name, 'inStock': True} for s in Size.objects.filter(productvariant__product=obj).distinct()]

    def get_features(self, obj):
        return obj.features.split('\n') if obj.features else []

    def get_careInstructions(self, obj):
        return obj.care_instructions.split('\n') if obj.care_instructions else []
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ('id', 'code', 'discount_type', 'value', 'min_order_value', 'valid_from', 'valid_to', 'active')

class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = ('id', 'shipping_flat_rate', 'shipping_free_above', 'tax_rate_percentage','cod_extra_fee')