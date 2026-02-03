import razorpay
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics, status, views, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, OrderSerializer, SavedAddressSerializer
from store.models import Product, ProductVariant, SiteConfig
from accounts.models import SavedAddress

# 🔥 IMPORT PAYMENT HELPERS
from payments.razorpay_client import (
    create_order as razorpay_create_order, 
    refund_payment, 
    verify_payment_signature 
)

# Initialize Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# ==========================================
# 1. ORDER MANAGEMENT (List, Status, Update)
# ==========================================

class UserOrdersView(generics.ListAPIView):
    """List all orders for the logged-in user."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items").order_by("-created_at")

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def order_status(request, pk):
    """
    GET /orders/<pk>/status/ -> Used by frontend polling to check payment status
    """
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    return Response({
        "order_id": order.id,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_payment_id": order.razorpay_payment_id,
    })

@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_order_status(request, pk):
    """Admin endpoint to update order status."""
    try:
        order = Order.objects.get(pk=pk) # Admin can access any order
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=404)
    
    if not request.user.is_staff:
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
    
    new_status = request.data.get("order_status")
    order.order_status = new_status
    order.save()
    return Response({"message": "Status updated"})

# ==========================================
# 2. PAYMENT VERIFICATION (Stock Deduction)
# ==========================================

class VerifyPaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        # 1. Get the Order
        try:
            # Lock the row to prevent race conditions
            order = Order.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == 'Paid':
             return Response({"message": "Order already processed"}, status=status.HTTP_200_OK)

        # 2. Verify Signature
        try:
            verify_payment_signature(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature
            )
        except Exception as e:
            order.payment_status = 'Failed'
            order.save()
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Success! Update Order Status
        order.payment_status = 'Paid'
        order.order_status = 'Processing'
        order.razorpay_payment_id = razorpay_payment_id
        order.save()

        # 4. 🔥 DEDUCT STOCK
        # We parse the label "Color / Size" generated in CheckoutView
        for item in order.items.all():
            try:
                # Expected format from Checkout: "Blue / M"
                parts = item.variant_label.split(' / ')
                if len(parts) == 2:
                    color_name = parts[0]
                    size_name = parts[1]
                    
                    variant = ProductVariant.objects.select_for_update().get(
                        product__title=item.product_name,
                        color__name=color_name,
                        size__name=size_name
                    )
                    
                    if variant.stock >= item.quantity:
                        variant.stock -= item.quantity
                        variant.save()
                    else:
                        print(f"CRITICAL STOCK ERROR: Order {order.id} - Variant {variant} out of stock")
            except Exception as e:
                print(f"Stock Deduction Error for item {item}: {e}")

        # 5. Clear Cart
        Cart.objects.filter(user=request.user).delete()

        return Response({"message": "Payment verified and Order Placed"}, status=status.HTTP_200_OK)

# ==========================================
# 3. ACTIONS (Cancel, Return, Exchange)
# ==========================================

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if order.order_status in ['Shipped', 'Delivered', 'Cancelled', 'Refund Initiated']:
        return Response({"error": "Order cannot be cancelled at this stage."}, status=status.HTTP_400_BAD_REQUEST)

    # Auto-Refund if Paid
    if order.payment_status == 'Paid' and order.razorpay_payment_id:
        try:
            refund_resp = refund_payment(
                payment_id=order.razorpay_payment_id,
                amount=float(order.total_amount),
                notes={"reason": "User requested cancellation"}
            )
            order.razorpay_refund_id = refund_resp.get('id')
            order.payment_status = 'Refunded'
            order.order_status = 'Cancelled'
            order.save()
            return Response({"status": "success", "message": "Order cancelled and refund initiated."})
        except Exception as e:
            return Response({"error": "Cancellation failed during refund."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Cancel if Unpaid/COD
    order.order_status = 'Cancelled'
    order.save()
    return Response({"status": "success", "message": "Order cancelled."})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def request_return_exchange_item(request, item_id):
    # Find item belonging to user's order
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    # Validation
    if item.order.order_status != 'Delivered':
        return Response({"error": "Order must be delivered first."}, status=status.HTTP_400_BAD_REQUEST)

    if item.status != 'Ordered':
        return Response({"error": "Request already submitted or processed."}, status=status.HTTP_400_BAD_REQUEST)

    # Get Data
    action_type = request.data.get('type')
    reason = request.data.get('reason')
    video_file = request.FILES.get('video')

    if not reason or not video_file:
        return Response({"error": "Reason and Video Proof are mandatory."}, status=status.HTTP_400_BAD_REQUEST)

    # Save
    item.return_reason = reason
    item.return_proof_video = video_file
    
    if action_type == 'return':
        item.status = 'Return Requested'
    elif action_type == 'exchange':
        item.status = 'Exchange Requested'
    else:
        return Response({"error": "Invalid action type"}, status=status.HTTP_400_BAD_REQUEST)
    
    item.save()
    return Response({"status": "success", "message": f"{action_type.capitalize()} request submitted."})

# ==========================================
# 4. CHECKOUT (Create Order) - 🔥 UPDATED FOR COD
# ==========================================

class CheckoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        items_payload = request.data.get("items")
        payment_method = request.data.get("payment_method", "Online") # 🔥 Get Payment Method

        if not items_payload:
            return Response({"error": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Fetch Site Config
        config = SiteConfig.objects.first()
        shipping_flat = config.shipping_flat_rate if config else 100
        free_shipping_limit = config.shipping_free_above if config else 2000
        tax_percent = config.tax_rate_percentage if config else 18
        cod_fee = config.cod_extra_fee if config else 50
        subtotal = Decimal("0.00")
        order_line_items = []

        # 2. Process Items
        for line in items_payload:
            raw_id = line.get("product_id")
            size_name = line.get("size")
            color_name = line.get("color") 
            quantity = int(line.get("quantity", 1) or 1)
            
            if not raw_id:
                return Response({"error": "Product ID is missing"}, status=status.HTTP_400_BAD_REQUEST)

            # Step A: Find Product
            try:
                product_obj = Product.objects.get(id=raw_id)
            except Product.DoesNotExist:
                return Response({"error": f"Product ID {raw_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Step B: Find Variant
            try:
                variant = ProductVariant.objects.get(
                    product=product_obj, 
                    size__name=size_name, 
                    color__name=color_name
                )
            except ProductVariant.DoesNotExist:
                return Response(
                    {"error": f"Variant unavailable: {product_obj.title} ({color_name}/{size_name})"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Step C: Check Stock
            if variant.stock < quantity:
                return Response(
                    {"error": f"Out of stock: {variant.product.title} ({color_name}/{size_name})"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            final_price = variant.price_override if variant.price_override else variant.product.price
            subtotal += final_price * quantity

            order_line_items.append({
                "product_name": variant.product.title,
                "variant_label": f"{color_name} / {size_name}", 
                "price": final_price,
                "quantity": quantity,
                "variant_obj": variant # Keep ref to deduct stock for COD
            })

        # 3. Totals
        shipping_fee = 0 if subtotal >= free_shipping_limit else shipping_flat
        tax_amount = (subtotal * tax_percent) / 100
        total_amount = subtotal + tax_amount + shipping_fee

        if payment_method == 'COD':
            total_amount += cod_fee

        # 4. Create Order
        first_name = request.data.get('firstName') or request.data.get('first_name', '')
        last_name = request.data.get('lastName') or request.data.get('last_name', '')
        address = request.data.get('address', '')
        apartment = request.data.get('apartment', '')
        city = request.data.get('city', '')
        state = request.data.get('state', '')
        zip_code = request.data.get('zip_code') or request.data.get('pinCode', '')
        country = request.data.get('country', 'India')
        phone = request.data.get('phone', '')
        
        shipping_addr = f"{first_name} {last_name}\n{address}"
        if apartment:
            shipping_addr += f"\n{apartment}"
        shipping_addr += f"\n{city}, {state} - {zip_code}\n{country}".strip()

        # 🔥 Determine Status based on Method
        # COD -> 'Pending' Payment, 'Processing' Order (Confirmed)
        # Online -> 'Pending' Payment, 'Pending' Order (Until Verified)
        initial_order_status = 'Processing' if payment_method == 'COD' else 'Pending'

        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_addr,
            phone=phone,
            total_amount=total_amount,
            payment_status='Pending',
            order_status=initial_order_status, 
            payment_method=payment_method # 🔥 Save Method (Ensure model has this field)
        )

        for item in order_line_items:
            OrderItem.objects.create(
                order=order,
                product_name=item["product_name"],
                variant_label=item["variant_label"],
                price=item["price"],
                quantity=item["quantity"],
            )
            
            # 🔥 DEDUCT STOCK IMMEDIATELY FOR COD
            if payment_method == 'COD':
                variant = item['variant_obj']
                variant.stock -= item['quantity']
                variant.save()

        # 5. Response Logic
        if payment_method == 'COD':
            # Clear Cart for COD immediately
            Cart.objects.filter(user=request.user).delete()
            
            return Response({
                "id": order.id,
                "message": "Order placed successfully via Cash on Delivery!",
                "payment_method": "COD",
                "order_status": order.order_status,
                "total_amount": total_amount,
            }, status=status.HTTP_201_CREATED)

        else:
            # Online: Create Razorpay Order
            try:
                rzp_order = razorpay_create_order(total_amount, currency="INR")
            except Exception as exc:
                return Response({"error": "Failed to create Razorpay order", "details": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

            order.razorpay_order_id = rzp_order.get("id")
            order.save()

            return Response({
                "id": order.id,
                "razorpay_order_id": order.razorpay_order_id,
                "amount": rzp_order.get("amount"),
                "currency": "INR",
                "key": getattr(settings, "RAZORPAY_KEY_ID", ""),
                "payment_method": "Online",
                "order_status": order.order_status,
            }, status=status.HTTP_201_CREATED)

# ... (Keep Cart & Address Views Unchanged) ...
class CartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

class AddToCartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        cart, _ = Cart.objects.get_or_create(user=request.user)
        variant = get_object_or_404(ProductVariant, id=variant_id)
        
        if variant.stock < quantity:
            return Response({"error": "Not enough stock available"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        if not created: cart_item.quantity += quantity
        else: cart_item.quantity = quantity
        cart_item.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

class RemoveCartItemView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk, cart__user=request.user)
        cart_item.delete()
        cart = Cart.objects.get(user=request.user)
        return Response(CartSerializer(cart).data)

class SavedAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SavedAddress.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SavedAddress.objects.filter(user=self.request.user)