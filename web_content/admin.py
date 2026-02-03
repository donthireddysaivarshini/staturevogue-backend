from django.contrib import admin
from .models import AnnouncementBar, HeroSlide, BrandStory, BrandFeature

@admin.register(AnnouncementBar)
class AnnouncementBarAdmin(admin.ModelAdmin):
    list_display = ('text', 'is_active')
    list_editable = ('is_active',)

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')

@admin.register(BrandFeature)
class BrandFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')

admin.site.register(BrandStory)