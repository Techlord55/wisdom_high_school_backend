# Location: .\apps\settings\models.py
# ==================== apps/settings/models.py ====================
from django.db import models
from apps.common.models import TimeStampedModel


class SystemSettings(TimeStampedModel):
    """System-wide settings model."""
    
    # General Settings
    school_name = models.CharField(max_length=255, default='Wisdom High School')
    academic_year = models.CharField(max_length=20, default='2024/2025')
    current_term = models.CharField(max_length=20, default='Term 1')
    
    # Notification Settings
    email_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=False)
    
    # Security Settings
    two_factor_auth_required = models.BooleanField(default=False)
    password_expiry_days = models.IntegerField(default=90)
    
    # Additional metadata
    last_backup_date = models.DateTimeField(blank=True, null=True)
    last_cache_clear_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"System Settings - {self.school_name}"
    
    @classmethod
    def get_settings(cls):
        """Get or create system settings singleton."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of settings."""
        pass
