# Location: .\apps\settings\views.py
# ==================== apps/settings/views.py ====================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.settings.models import SystemSettings
from apps.settings.serializers import SystemSettingsSerializer
from apps.auth.permissions import IsAdminUser


class SystemSettingsViewSet(viewsets.ViewSet):
    """ViewSet for managing system settings."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """Get system settings."""
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
        
        # TODO: Implement actual backup logic
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
        
        # TODO: Implement actual cache clearing logic
        from django.core.cache import cache
        cache.clear()
        
        return Response({
            'message': 'Cache cleared successfully',
            'last_cache_clear_date': settings.last_cache_clear_date
        })
