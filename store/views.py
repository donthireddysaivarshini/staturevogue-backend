from rest_framework import generics, permissions, serializers
from django.db.models import Q
from .models import Product, Category, Collection, Review
from .serializers import ProductSerializer, CategorySerializer, CollectionSerializer, ReviewSerializer

# --- 1. PRODUCTS API ---
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'variants')
        
        # Filters
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(gender__iexact=gender)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

        collection = self.request.query_params.get('collection')
        if collection:
            queryset = queryset.filter(Q(collections__slug=collection) | Q(collections__title__icontains=collection))

        badge = self.request.query_params.get('badge')
        if badge:
            if badge.lower() == 'new': queryset = queryset.filter(badge='NEW')
            elif badge.lower() == 'bestseller': queryset = queryset.filter(badge='BESTSELLER')

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return queryset.distinct()

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'

# --- 2. CATEGORIES API (UPDATED) ---
class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.all()
        
        # Featured Filter
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # 🔥 FIX: Filter Categories based on the requested Gender
        gender = self.request.query_params.get('gender')
        if gender:
            # If requesting "Women", return "Women" + "All"
            # If requesting "Men", return "Men" + "All"
            queryset = queryset.filter(Q(gender__iexact=gender) | Q(gender='All'))
            
        return queryset

# --- 3. COLLECTIONS API (UPDATED) ---
class CollectionListView(generics.ListAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        queryset = Collection.objects.filter(is_active=True)
        
        # 🔥 FIX: Filter Collections based on the requested Gender
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(Q(gender__iexact=gender) | Q(gender='All'))
            
        return queryset

# --- 4. REVIEWS API ---
class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        slug = self.kwargs['slug']
        return Review.objects.filter(product__slug=slug).order_by('-created_at')

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
             raise serializers.ValidationError("You must be logged in to post a review.")
        slug = self.kwargs['slug']
        # Use get_object_or_404 is safer, but standard get is fine if slug is valid
        product = Product.objects.get(slug=slug)
        serializer.save(product=product)