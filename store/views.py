from rest_framework import generics, permissions, serializers
from django.db.models import Q
from .models import Product, Category, Collection, Review
from .serializers import ProductSerializer, CategorySerializer, CollectionSerializer, ReviewSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from decimal import Decimal
from .models import Coupon, SiteConfig
from .serializers import SiteConfigSerializer

# --- 1. PRODUCTS API ---
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

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
            # 🔥 UPDATED SEARCH LOGIC
            # 1. Search in Title
            # 2. Search in Description
            # 3. Search in Variant SKUs (Product Codes)
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(variants__sku__icontains=search) # <--- Added SKU Search
            ).distinct() # Distinct is important because joining variants can duplicate rows

        return queryset

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
class ValidateCouponView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        order_total = Decimal(request.data.get('order_total', 0))
        
        if not code:
            return Response({'error': 'Coupon code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=code, active=True)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code'}, status=status.HTTP_404_NOT_FOUND)
        
        now = timezone.now()
        if coupon.valid_from > now or coupon.valid_to < now:
            return Response({'error': 'Coupon has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        if order_total < coupon.min_order_value:
            return Response({
                'error': f'Minimum order value of ₹{coupon.min_order_value} required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if coupon.uses_count >= coupon.usage_limit:
            return Response({'error': 'Coupon usage limit exceeded'}, status=status.HTTP_400_BAD_REQUEST)
        
        discount = 0
        if coupon.discount_type == 'percentage':
            discount = (order_total * coupon.value) / 100
        else:
            discount = coupon.value
        
        return Response({
            'success': True,
            'discount': float(discount),
            'discount_type': coupon.discount_type,
            'coupon_value': float(coupon.value),
            'message': f'Coupon applied successfully! You saved ₹{discount}'
        }, status=status.HTTP_200_OK)

class SiteConfigView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        config = SiteConfig.objects.first()
        if not config:
            config = SiteConfig.objects.create()
        
        serializer = SiteConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)