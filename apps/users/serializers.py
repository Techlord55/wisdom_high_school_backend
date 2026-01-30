# Location: .\apps\users\serializers.py
# ==================== apps/users/serializers.py ====================
from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'clerk_id', 'email', 'first_name', 'last_name',
            'full_name', 'phone_number', 'role', 'sex', 'place_of_birth',
            'date_of_birth', 'avatar_url', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'clerk_id', 'email', 'created_at', 'updated_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer - allows updating profile information."""
    
    date_of_birth = serializers.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', 'iso-8601'],
        format='%Y-%m-%d'
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'sex',
            'place_of_birth', 'date_of_birth', 'role'
        ]
        extra_kwargs = {
            'role': {'required': False}  # Role is optional in updates
        }
