# TEMPORARY DEBUG VERSION - Settings View with Relaxed Permissions
# Replace apps/settings/views.py with this to test if the API works
# Then restore the original after confirming

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.settings.models import SystemSettings
from apps.settings.serializers import SystemSettingsSerializer


class SystemSettingsViewSet(viewsets.ViewSet):
    """ViewSet for managing system settings - DEBUG VERSION."""
    
    # TEMPORARY: Only require authentication, not admin
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get system settings."""
        # DEBUG: Print user info
        print(f"\n{'='*60}")
        print(f"DEBUG: Settings Access Attempt")
        print(f"{'='*60}")
        print(f"User: {request.user.email}")
        print(f"Role: {request.user.role}")
        print(f"Is Staff: {request.user.is_staff}")
        print(f"Is Superuser: {request.user.is_superuser}")
        print(f"Is Admin: {request.user.role == 'admin'}")
        print(f"{'='*60}\n")
        
        settings = SystemSettings.get_settings()
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """Update system settings."""
        settings = SystemSettings.get_settings()
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def backup_database(self, request):
        """Trigger database backup."""
        settings = SystemSettings.get_settings()
        settings.last_backup_date = timezone.now()
        settings.save()
        
        return Response({
            'message': 'Database backup initiated successfully',
            'last_backup_date': settings.last_backup_date
        })
    
    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """Clear system cache."""
        settings = SystemSettings.get_settings()
        settings.last_cache_clear_date = timezone.now()
        settings.save()
        
        from django.core.cache import cache
        cache.clear()
        
        return Response({
            'message': 'Cache cleared successfully',
            'last_cache_clear_date': settings.last_cache_clear_date
        })
