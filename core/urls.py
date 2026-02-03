from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# We don't have the router setup yet, so we will comment it out for now to avoid errors
# from web_content.views import WebContentViewSet
# from rest_framework.routers import DefaultRouter
# router = DefaultRouter()
# router.register(r'content', WebContentViewSet, basename='content')

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # --- Connect the Apps ---
    path("api/auth/", include("accounts.urls")),
    path("api/store/", include("store.urls")),   # Uncomment when store app is ready
    path("api/orders/", include("orders.urls")), # Uncomment when orders app is ready
    path('accounts/', include('allauth.urls')),
    path('api/content/', include('web_content.urls'))
]


# Serve media files in development (images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)