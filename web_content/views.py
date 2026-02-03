from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import AnnouncementBar, HeroSlide, BrandStory, BrandFeature
from .serializers import (
    AnnouncementSerializer, HeroSlideSerializer, 
    BrandStorySerializer, BrandFeatureSerializer
)

class WebContentPublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Fetch active content
        announcement = AnnouncementBar.objects.filter(is_active=True).first()
        hero_slides = HeroSlide.objects.filter(is_active=True)
        brand_story = BrandStory.objects.filter(is_active=True).first()
        brand_features = BrandFeature.objects.filter(is_active=True)

        return Response({
            "announcement": AnnouncementSerializer(announcement).data if announcement else None,
            "hero_slides": HeroSlideSerializer(hero_slides, many=True, context={'request': request}).data,
            "brand_story": BrandStorySerializer(brand_story, context={'request': request}).data if brand_story else None,
            "brand_features": BrandFeatureSerializer(brand_features, many=True, context={'request': request}).data
        })