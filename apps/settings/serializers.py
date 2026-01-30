# Location: .\apps\settings\serializers.py
# ==================== apps/settings/serializers.py ====================
from rest_framework import serializers
from apps.settings.models import SystemSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for system settings."""
    
    class Meta:
        model = SystemSettings
        fields = [
            'id',
            'school_name',
            'academic_year',
            'current_term',
            'email_notifications_enabled',
            'sms_notifications_enabled',
            'two_factor_auth_required',
            'password_expiry_days',
            'last_backup_date',
            'last_cache_clear_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'last_backup_date', 'last_cache_clear_date', 'created_at', 'updated_at']
