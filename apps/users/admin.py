# Location: .\apps\users\admin.py
# ==================== apps/users/admin.py ====================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User admin configuration."""
    
    list_display = ['email', 'first_name', 'last_name', 'role', 'clerk_status', 'is_staff', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name', 'clerk_id']
    ordering = ['-created_at']
    actions = ['remove_clerk_link']
    
    fieldsets = (
        (None, {'fields': ('email', 'clerk_id', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 
                                      'sex', 'place_of_birth', 'date_of_birth', 'avatar_url')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'clerk_id', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    @admin.display(description='Clerk Status')
    def clerk_status(self, obj):
        """Display clerk integration status."""
        if not obj.clerk_id:
            return '❌ No Clerk ID'
        elif obj.clerk_id.startswith('local_'):
            return '🏠 Local Only'
        else:
            return '✅ Clerk Synced'
    
    @admin.action(description='Remove Clerk link (keep as local user)')
    def remove_clerk_link(self, request, queryset):
        """Remove Clerk ID from selected users."""
        import uuid
        for user in queryset:
            if user.clerk_id and not user.clerk_id.startswith('local_'):
                user.clerk_id = f'local_{uuid.uuid4().hex[:16]}'
                user.save()
        self.message_user(request, f'Removed Clerk link from {queryset.count()} user(s)')
