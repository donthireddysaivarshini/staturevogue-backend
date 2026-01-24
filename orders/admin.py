from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'variant_label', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'total_amount', 'shipping_address_preview', 'payment_status_badge', 'order_status')
    list_filter = ('payment_status', 'order_status', 'created_at')
    search_fields = ('user__email', 'razorpay_order_id', 'razorpay_payment_id')
    
    # ✅ Actions for Refund/Return/Exchange
    actions = [
        'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered',
        'mark_return_approved', 'mark_exchange_approved', 'mark_refunded'
    ]
    
    list_editable = ('order_status',)

    readonly_fields = (
        'user', 'total_amount', 'created_at',
        'shipping_address', 'phone',
        'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
        'razorpay_refund_id'
    )
    
    fieldsets = (
        ('Order Info', {'fields': ('user', 'total_amount', 'created_at')}),
        ('Status', {'fields': ('payment_status', 'order_status')}),
        ('Address', {'fields': ('shipping_address', 'phone')}),
        ('Payment Details', {'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_refund_id')}),
    )
    inlines = [OrderItemInline]

    # --- Actions ---
    @admin.action(description='Mark as Processing')
    def mark_as_processing(self, request, queryset):
        queryset.update(order_status='Processing')

    @admin.action(description='Mark as Shipped')
    def mark_as_shipped(self, request, queryset):
        queryset.update(order_status='Shipped')

    @admin.action(description='Mark as Delivered')
    def mark_as_delivered(self, request, queryset):
        queryset.update(order_status='Delivered')

    @admin.action(description='Approve Return Request')
    def mark_return_approved(self, request, queryset):
        queryset.update(order_status='Return Approved')

    @admin.action(description='Approve Exchange Request')
    def mark_exchange_approved(self, request, queryset):
        queryset.update(order_status='Exchange Approved')

    @admin.action(description='Mark as Refunded (Manual)')
    def mark_refunded(self, request, queryset):
        queryset.update(payment_status='Refunded', order_status='Refund Initiated')

    # --- Display Helpers ---
    def user_email(self, obj): return obj.user.email
    def shipping_address_preview(self, obj): return obj.shipping_address[:50] + "..." if obj.shipping_address else "-"
    def payment_status_badge(self, obj):
        colors = {'Paid': 'green', 'Pending': 'orange', 'Refunded': 'red'}
        color = colors.get(obj.payment_status, 'grey')
        return format_html(f'<span style="color:white;background:{color};padding:3px 8px;border-radius:3px;">{obj.payment_status}</span>')

admin.site.unregister(Cart) if Cart in admin.site._registry else None
admin.site.unregister(CartItem) if CartItem in admin.site._registry else None