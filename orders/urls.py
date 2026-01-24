from django.urls import path
from .views import (
    UserOrdersView, CheckoutView, VerifyPaymentView,
    cancel_order, request_return_exchange, # ✅ Import new views
    order_status, SavedAddressListCreateView, SavedAddressDetailView, # Existing
    CartView, AddToCartView, RemoveCartItemView # Existing
)

urlpatterns = [
    # Cart
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', AddToCartView.as_view(), name='cart-add'),
    path('cart/remove/<int:pk>/', RemoveCartItemView.as_view(), name='cart-remove'),

    # Order Management
    path('', UserOrdersView.as_view(), name='user-orders'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('<int:pk>/cancel/', cancel_order, name='cancel-order'), # ✅ Cancel
    path('<int:pk>/request-action/', request_return_exchange, name='return-exchange'), # ✅ Return/Exchange
    path('<int:pk>/status/', order_status, name='order-status'),

    # Addresses
    path('addresses/', SavedAddressListCreateView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', SavedAddressDetailView.as_view(), name='address-detail'),

    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
]