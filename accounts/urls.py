from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, CustomTokenObtainPairView, UserProfileView, GoogleLogin, SavedAddressViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'addresses', SavedAddressViewSet, basename='savedaddress')

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserProfileView.as_view(), name='user_profile'),
    # NEW: Google Login
    path('google/', GoogleLogin.as_view(), name='google_login'),
    # Addresses API (list/create/detail/update/delete + set-default)
    path('', include(router.urls)),
]