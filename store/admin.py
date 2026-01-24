from django.contrib import admin
from django.db import models # Needed for the checkbox fix
from django.forms import CheckboxSelectMultiple # Needed for the checkbox fix
from .models import Category, Collection, Color, Size, Product, ProductImage, ProductVariant, Review
from .models import Coupon, SiteConfig
# --- INLINES ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'color', 'alt_text']

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['sku', 'color', 'size', 'stock', 'price_override']

# --- PRODUCT ADMIN ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'gender', 'price', 'badge', 'in_stock')
    list_filter = ('category', 'gender', 'badge', 'collections')
    search_fields = ('title', 'description')
    inlines = [ProductImageInline, ProductVariantInline]
    prepopulated_fields = {'slug': ('title',)}
    
    # 🔥 FIX 1: Use Checkboxes for Collections (Easier than the arrow box)
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

# --- CATEGORY ADMIN ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_featured')
    list_editable = ('is_featured',)

# --- REVIEW ADMIN (Fixed Duplicate Registration) ---
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_user_name', 'get_user_email', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__title', 'user__username', 'user__email', 'comment')

    def get_user_name(self, obj):
        return obj.user.username if obj.user else obj.user_name
    get_user_name.short_description = 'User'

    def get_user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    get_user_email.short_description = 'Email'

# --- SIMPLE REGISTRATIONS ---
admin.site.register(Collection)
admin.site.register(Color)
admin.site.register(Size)
# admin.site.register(Review) <--- REMOVED THIS LINE (It caused the crash)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'active', 'valid_to')
    list_filter = ('active', 'discount_type')

@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = (
        'shipping_flat_rate',
        'shipping_free_above',
        'tax_rate_percentage',
     )
    def has_add_permission(self, request):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True