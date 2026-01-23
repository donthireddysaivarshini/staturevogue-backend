from django.urls import path
from .views import ProductListView, ProductDetailView, CategoryListView, CollectionListView,ProductReviewListCreateView

urlpatterns = [
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Configuration
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('products/<slug:slug>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
]