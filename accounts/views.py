from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.conf import settings

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    # SavedAddress serializer
    SavedAddressSerializer,
)
from .models import SavedAddress

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()

# --- 1. Standard Auth Views ---

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class SavedAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavedAddressSerializer

    def get_queryset(self):
        return SavedAddress.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def perform_create(self, serializer):
        # serializer.create will use request from context to attach user
        serializer.save()

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        addr = self.get_object()
        # Only owner can set default; get_object ensures queryset is user-scoped
        addr.is_default = True
        addr.save()  # model.save will unset others
        serializer = self.get_serializer(addr)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- 2. THE FINAL GOOGLE FIX ---

class CustomGoogleOAuth2Client(OAuth2Client):
    def __init__(self, *args, **kwargs):
        # Google expects spaces, not commas, for scopes. 
        # OAuth2Client defaults to space, but some versions force comma.
        # This ensures we use the default (space) or strip the argument.
        if "scope_delimiter" in kwargs:
            del kwargs["scope_delimiter"]
        super().__init__(*args, **kwargs)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = CustomGoogleOAuth2Client
    
    # Define it here for safety
    callback_url = "postmessage"

    def post(self, request, *args, **kwargs):
        # 🔥 CRITICAL FIX: 
        # The serializer validates 'callback_url'. If it's missing from the frontend payload,
        # it might fail validation before checking the view attribute.
        # We force it into the data here.
        try:
            # Handle QueryDict (mutable) vs Dict
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
                request.data['callback_url'] = "postmessage"
                request.data._mutable = False
            else:
                request.data['callback_url'] = "postmessage"
        except Exception as e:
            print(f"⚠️ Could not inject callback_url: {e}")

        # Call the standard logic
        response = super().post(request, *args, **kwargs)

        # Debugging: If it STILL fails, print why
        if response.status_code == 400:
            print("------------------------------------------------")
            print("❌ VALIDATION FAILED (Internal Django/Serializer Error)")
            print(f"Sent Code: {request.data.get('code')}")
            # If serializer exists, print its errors
            if hasattr(self, 'serializer') and self.serializer:
                print(f"Validation Errors: {self.serializer.errors}")
            else:
                print(f"Response Data: {response.data}")
            print("------------------------------------------------")
        
        return response
    def get_serializer_context(self):
        """
        Force 'postmessage' into the validator context.
        This fixes the "Define callback_url in view" error.
        """
        context = super().get_serializer_context()
        context["callback_url"] = "postmessage"
        return context