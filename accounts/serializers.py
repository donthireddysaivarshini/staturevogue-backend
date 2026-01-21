from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import SavedAddress

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'first_name')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'phone')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            phone=validated_data.get('phone', '')
        )
        return user

# Custom Login Response (Adds user data to the JWT token response)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'email': self.user.email,
            'name': self.user.first_name,
            'id': self.user.id
        }
        return data


class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = ('id', 'label', 'first_name', 'last_name', 'address', 'apartment', 'city', 'state', 'zip_code', 'country', 'phone', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        # When creating a new address, ensure the user doesn't exceed 3 addresses
        if self.instance is None and user and user.is_authenticated:
            existing_count = SavedAddress.objects.filter(user=user).count()
            if existing_count >= 3:
                raise serializers.ValidationError('You can save up to 3 addresses only.')

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError('Authentication required')

        # If is_default is True, the model.save will clear previous defaults
        addr = SavedAddress.objects.create(user=user, **validated_data)
        return addr

    def update(self, instance, validated_data):
        # Let the model save() handle toggling defaults when is_default=True
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance