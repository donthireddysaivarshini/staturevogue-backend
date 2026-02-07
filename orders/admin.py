from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from .models import Order, OrderItem, Cart, CartItem
from payments.razorpay_client import refund_payment

# --- INLINE ITEMS ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'variant_label', 'price', 'quantity', 'status', 'return_reason', 'video_preview', 'admin_comment', 'exchange_coupon')
    readonly_fields = ('product_name', 'variant_label', 'price', 'quantity', 'return_reason', 'video_preview', 'exchange_coupon')
    can_delete = False

    def video_preview(self, obj):
        if obj.return_proof_video:
            return format_html(
                '<a href="{}" target="_blank" style="color:blue; font-weight:bold;">View Video</a>',
                obj.return_proof_video.url
            )
        return "-"
    video_preview.short_description = "Proof"

# --- ORDER ADMIN ---
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Register the action
    actions = ['process_refund_return', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    list_per_page = 20
    list_display = ('id', 'user_email', 'total_amount', 'payment_status_badge', 'order_status', 'created_at','request_alert','payment_method_badge','tracking_link')
    list_filter = ('payment_method','payment_status', 'order_status', 'created_at')
    
    def payment_method_badge(self, obj):
        if obj.payment_method == 'COD':
            return format_html('<b style="color:#1F2B5B;">📦 COD</b>')
        return format_html('<span style="color:purple;">💳 Online</span>')
    payment_method_badge.short_description = "Method"

    # 🔥 UPDATED REFUND LOGIC: Splits Auto (Pre-delivery) vs Manual (Post-delivery)
    @admin.action(description='💰 Process Refund (Smart Mode)')
    def process_refund_return(self, request, queryset):
        for order in queryset:
            if order.payment_status == 'Refunded':
                self.message_user(request, f"Order #{order.id} is already refunded.", messages.WARNING)
                continue

            # SCENARIO A: Pre-Delivery Cancellation (Full Auto Refund)
            # Only if status is NOT Delivered/Returned yet
            if order.payment_method == 'Online' and order.payment_status == 'Paid' and order.order_status in ['Processing', 'Pending', 'Confirmed']:
                try:
                    refund_resp = refund_payment(
                        payment_id=order.razorpay_payment_id,
                        amount=float(order.total_amount),
                        notes={"reason": "Admin processed cancellation"}
                    )
                    order.razorpay_refund_id = refund_resp.get('id')
                    order.payment_status = 'Refunded'
                    order.order_status = 'Cancelled'
                    order.refunded_at = timezone.now()
                    order.save()
                    self.message_user(request, f"✅ Auto-Refund (Full) successful for Order #{order.id}", messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"❌ Razorpay Error for Order #{order.id}: {str(e)}", messages.ERROR)

            # SCENARIO B: Post-Delivery Return (MANUAL Refund - NO Razorpay)
            # This applies to: Delivered, Return Requested, Return Approved
            # We do NOT call refund_payment() here to allow Admin to deduct shipping manually via Bank Transfer
            elif order.order_status in ['Delivered', 'Return Requested', 'Return Approved', 'Returned']:
                order.payment_status = 'Refunded'
                order.order_status = 'Refunded'
                order.refunded_at = timezone.now()
                # We do NOT generate a razorpay_refund_id, marking it as Manual
                order.save()
                
                method_txt = "Dashboard" if order.payment_method == 'Online' else "Bank Transfer"
                self.message_user(request, f"✅ Marked Order #{order.id} as Refunded. Please refund manually via {method_txt} (Deduct Shipping).", messages.SUCCESS)
            
            # SCENARIO C: COD Delivered
            elif order.payment_method == 'COD' and order.order_status == 'Delivered':
                order.payment_status = 'Refunded'
                order.order_status = 'Refunded'
                order.refunded_at = timezone.now()
                order.save()
                self.message_user(request, f"✅ Marked Order #{order.id} (COD) as Refunded manually.", messages.SUCCESS)

            else:
                self.message_user(request, f"⚠️ Order #{order.id} status '{order.order_status}' not handled by smart refund.", messages.WARNING)

    def request_alert(self, obj):
        pending_count = obj.items.filter(status__in=['Return Requested', 'Exchange Requested']).count()
        if pending_count > 0:
            return format_html(
                '<span style="background-color:#ff4444; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">'
                f'🔥 {pending_count} REQUEST(S)'
                '</span>'
            )
        return "-"
    request_alert.short_description = "Actions Pending"
    
    search_fields = ('user__email', 'razorpay_order_id', 'id')
    list_editable = ('order_status', 'tracking_link')
    readonly_fields = ('user', 'total_amount', 'created_at', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'razorpay_refund_id')

    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'total_amount', 'created_at')
        }),
        ('Status', {
            'fields': ('payment_status', 'order_status') 
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'phone')
        }),
        ('Payment Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_refund_id'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [OrderItemInline]

    @admin.action(description='Mark as Processing')
    def mark_as_processing(self, request, queryset):
        queryset.update(order_status='Processing')

    @admin.action(description='Mark as Shipped')
    def mark_as_shipped(self, request, queryset):
        queryset.update(order_status='Shipped')

    @admin.action(description='Mark as Delivered')
    def mark_as_delivered(self, request, queryset):
        queryset.update(order_status='Delivered')

    def user_email(self, obj): return obj.user.email
    
    def payment_status_badge(self, obj):
        colors = {'Paid': 'green', 'Pending': 'orange', 'Refunded': 'purple', 'Failed': 'red'}
        color = colors.get(obj.payment_status, 'grey')
        return format_html(f'<span style="color:white;background:{color};padding:3px 8px;border-radius:3px;">{obj.payment_status}</span>')

# Unregister Cart to keep admin clean
try:
    admin.site.unregister(Cart)
    admin.site.unregister(CartItem)
except admin.sites.NotRegistered:
    pass