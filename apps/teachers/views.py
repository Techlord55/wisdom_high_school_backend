# Location: .\apps\teachers\views.py
# ==================== apps/teachers/views.py ====================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.teachers.models import Teacher
from apps.teachers.serializers import (
    TeacherSerializer, 
    TeacherCreateSerializer,
    TeacherUpdateSerializer
)
from apps.teachers.clerk_sync import (
    delete_teacher_from_clerk,
    update_teacher_password_in_clerk
)
from apps.common.permissions import IsAdmin
from apps.common.utils import error_response, success_response
import json


class TeacherViewSet(viewsets.ModelViewSet):
    """Teacher viewset - Admin can create, all authenticated users can view."""
    
    queryset = Teacher.objects.select_related('user').all()
    serializer_class = TeacherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['department', 'specialization']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return TeacherCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeacherUpdateSerializer
        return TeacherSerializer
    
    def get_permissions(self):
        """Only admins can create, update, or delete teachers."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'teacher':
            # Teachers can only see their own profile
            return Teacher.objects.filter(user=user)
        
        # Admins and students can see all teachers
        return Teacher.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        """Delete teacher and also remove from Clerk."""
        teacher = self.get_object()
        clerk_id = teacher.user.clerk_id
        
        try:
            # Delete from our database first
            teacher.delete()
            
            # Then delete from Clerk
            if clerk_id:
                delete_teacher_from_clerk(clerk_id)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return error_response(
                f'Failed to delete teacher: {str(e)}',
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current teacher profile."""
        try:
            teacher = Teacher.objects.get(user=request.user)
            serializer = self.get_serializer(teacher)
            return Response(serializer.data)
        except Teacher.DoesNotExist:
            return error_response('Teacher profile not found', status=404)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_classes(self, request, pk=None):
        """Assign classes to a teacher (admin only)."""
        teacher = self.get_object()
        classes = request.data.get('classes', [])
        
        teacher.classes_assigned = classes
        teacher.save()
        
        return success_response(
            TeacherSerializer(teacher).data,
            'Classes assigned successfully'
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_subjects(self, request, pk=None):
        """Assign subjects to a teacher (admin only)."""
        teacher = self.get_object()
        subjects = request.data.get('subjects', [])
        
        teacher.subjects = subjects
        teacher.save()
        
        return success_response(
            TeacherSerializer(teacher).data,
            'Subjects assigned successfully'
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def set_hours(self, request, pk=None):
        """Set teaching hours for a teacher (admin only)."""
        teacher = self.get_object()
        hours = request.data.get('hours_per_week')
        
        if hours is None:
            return error_response('hours_per_week is required')
        
        teacher.hours_per_week = hours
        teacher.save()
        
        return success_response(
            TeacherSerializer(teacher).data,
            'Teaching hours updated successfully'
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def set_password(self, request, pk=None):
        """Set password for a teacher (admin only)."""
        teacher = self.get_object()
        password = request.data.get('password')
        
        if not password:
            return error_response('password is required')
        
        # Validate password length
        if len(password) < 8:
            return error_response('Password must be at least 8 characters long')
        
        try:
            # Update password in Clerk
            clerk_id = teacher.user.clerk_id
            if not clerk_id:
                return error_response('Teacher is not synced with Clerk')
            
            update_teacher_password_in_clerk(clerk_id, password)
            
            return success_response(
                {'message': 'Password updated successfully'},
                'Password updated successfully'
            )
        except Exception as e:
            error_message = str(e)
            
            # Parse Clerk error for better user experience
            if 'form_password_pwned' in error_message:
                return error_response(
                    'This password has been found in a data breach and is not secure. Please use a stronger, unique password.',
                    status=400
                )
            elif 'form_password_length_too_short' in error_message:
                return error_response(
                    'Password is too short. Please use at least 8 characters.',
                    status=400
                )
            elif 'form_password_not_strong_enough' in error_message:
                return error_response(
                    'Password is not strong enough. Please use a mix of uppercase, lowercase, numbers, and special characters.',
                    status=400
                )
            else:
                return error_response(
                    f'Failed to update password: {error_message}',
                    status=500
                )
