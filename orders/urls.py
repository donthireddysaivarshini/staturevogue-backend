from django.urls import path
from .views import (
    UserOrdersView, CheckoutView, VerifyPaymentView, update_order_status,
    cancel_order, request_return_exchange_item,  # ✅ Imported directly
    order_status, SavedAddressListCreateView, SavedAddressDetailView,
    CartView, AddToCartView, RemoveCartItemView
)

urlpatterns = [
    # --- CART ---
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', AddToCartView.as_view(), name='cart-add'),
    path('cart/remove/<int:pk>/', RemoveCartItemView.as_view(), name='cart-remove'),

    # --- ORDER MANAGEMENT ---
    path('', UserOrdersView.as_view(), name='user-orders'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Order Level Actions
    path('<int:pk>/cancel/', cancel_order, name='cancel-order'),
    path('<int:pk>/status/', order_status, name='order-status'),

    # ✅ ITEM LEVEL RETURN/EXCHANGE (Corrected line)
    # Removing 'views.' prefix because it is imported directly above
 path('items/<int:item_id>/request-action/', request_return_exchange_item, name='item-action'),

    # --- PAYMENTS ---
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),

    # --- ADDRESSES ---
    path('addresses/', SavedAddressListCreateView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', SavedAddressDetailView.as_view(), name='address-detail'),
]