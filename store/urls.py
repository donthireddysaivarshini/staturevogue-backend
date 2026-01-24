from django.urls import path
from .views import ProductListView, ProductDetailView, CategoryListView, CollectionListView,ProductReviewListCreateView
from .views import ValidateCouponView, SiteConfigView
urlpatterns = [
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Configuration
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('products/<slug:slug>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
    path('validate-coupon/', ValidateCouponView.as_view(), name='validate_coupon'),
    path('config/', SiteConfigView.as_view(), name='site_config'),
]