# Location: .\apps\settings\admin.py
# ==================== apps/settings/admin.py ====================
from django.contrib import admin
from apps.settings.models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin interface for system settings."""
    
    list_display = [
        'school_name',
        'academic_year',
        'current_term',
        'email_notifications_enabled',
        'sms_notifications_enabled',
        'updated_at',
    ]
    
    fieldsets = (
        ('General Settings', {
            'fields': ('school_name', 'academic_year', 'current_term')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications_enabled', 'sms_notifications_enabled')
        }),
        ('Security Settings', {
            'fields': ('two_factor_auth_required', 'password_expiry_days')
        }),
        ('Maintenance', {
            'fields': ('last_backup_date', 'last_cache_clear_date'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Only allow one settings instance."""
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings."""
        return False
