# Location: .\apps\teachers\serializers.py
# ==================== apps/teachers/serializers.py ====================
from rest_framework import serializers
from apps.teachers.models import Teacher
from apps.users.serializers import UserSerializer
from apps.teachers.clerk_sync import create_teacher_in_clerk, delete_teacher_from_clerk
from django.utils.crypto import get_random_string


class TeacherSerializer(serializers.ModelSerializer):
    """Teacher serializer."""
    
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'user', 'teacher_id', 'full_name', 'email',
            'department', 'specialization', 'years_of_experience', 
            'phone_number', 'salary_amount', 'subjects', 
            'classes_assigned', 'hours_per_week',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher_id', 'created_at', 'updated_at']


class TeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teacher profiles (admin only)."""
    
    # Include user fields for creating both user and teacher profile
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        help_text="Optional initial password. If not provided, a temporary password will be generated."
    )
    send_invitation = serializers.BooleanField(
        write_only=True,
        default=False,
        help_text="If true, sends an invitation email to the teacher"
    )
    
    class Meta:
        model = Teacher
        fields = [
            'email', 'first_name', 'last_name', 'password', 'send_invitation',
            'department', 'specialization', 'years_of_experience',
            'phone_number', 'salary_amount', 'subjects',
            'classes_assigned', 'hours_per_week'
        ]
    
    def create(self, validated_data):
        from apps.users.models import User
        
        # Extract user data
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password', None)
        send_invitation = validated_data.pop('send_invitation', False)
        
        # Generate a temporary password if none provided
        if not password:
            password = get_random_string(16)
        
        try:
            # Create user in Clerk first
            clerk_user = create_teacher_in_clerk(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                send_invitation=send_invitation
            )
            
            # Create user in our database with Clerk ID
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='teacher',
                clerk_id=clerk_user['id']
            )
            
            # Create teacher profile
            teacher = Teacher.objects.create(user=user, **validated_data)
            
            return teacher
            
        except Exception as e:
            # If Clerk creation fails, don't create the user in our DB
            raise serializers.ValidationError({
                'error': f'Failed to create teacher in Clerk: {str(e)}'
            })


class TeacherUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating teacher profiles."""
    
    class Meta:
        model = Teacher
        fields = [
            'department', 'specialization', 'years_of_experience',
            'phone_number', 'salary_amount', 'subjects',
            'classes_assigned', 'hours_per_week'
        ]
