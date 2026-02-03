from rest_framework import serializers
from .models import AnnouncementBar, HeroSlide, BrandStory, BrandFeature

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementBar
        fields = ['text']

class HeroSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSlide
        fields = ['id', 'image', 'title', 'subtitle', 'button_text', 'button_link']

class BrandStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandStory
        fields = ['heading', 'content', 'image_1', 'image_2']

class BrandFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandFeature
        fields = ['title', 'icon_image']