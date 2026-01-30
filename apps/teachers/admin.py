# ==================== apps/teachers/admin.py ====================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from apps.teachers.models import Teacher
from apps.users.models import User


class TeacherUserInline(admin.StackedInline):
    """Inline form to edit User details within Teacher admin."""
    model = User
    can_delete = False
    verbose_name_plural = 'User Account'
    fk_name = 'teacher_profile'
    fields = ('email', 'first_name', 'last_name', 'phone_number', 'sex', 
              'date_of_birth', 'place_of_birth', 'is_active')
    readonly_fields = ('email',)
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Teacher admin configuration."""
    
    list_display = ['teacher_id', 'get_full_name', 'get_email', 'department', 
                    'specialization', 'years_of_experience', 'get_is_active', 'created_at']
    list_filter = ['department', 'specialization', 'user__is_active']
    search_fields = ['teacher_id', 'user__email', 'user__first_name', 'user__last_name', 'department']
    readonly_fields = ['teacher_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('teacher_id', 'user', 'department', 'specialization', 'years_of_experience')
        }),
        ('Contact & Salary', {
            'fields': ('phone_number', 'salary_amount')
        }),
        ('Teaching Assignments', {
            'fields': ('subjects', 'classes_assigned', 'hours_per_week')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Display methods
    @admin.display(description='Full Name', ordering='user__first_name')
    def get_full_name(self, obj):
        return obj.user.full_name
    
    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email
    
    @admin.display(description='Active', boolean=True, ordering='user__is_active')
    def get_is_active(self, obj):
        return obj.user.is_active
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user."""
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    # Custom action to reset password
    @admin.action(description='Reset password for selected teachers')
    def reset_password(self, request, queryset):
        """Reset password to a temporary value."""
        temp_password = 'TempPassword123!'
        count = 0
        
        for teacher in queryset:
            teacher.user.set_password(temp_password)
            teacher.user.save()
            count += 1
        
        self.message_user(
            request,
            f'Password reset to "{temp_password}" for {count} teacher(s). '
            f'Please ask them to change it on first login.'
        )
    
    actions = ['reset_password']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter users to only show teacher role users."""
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(role='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Ensure user has teacher role when saving."""
        if obj.user.role != 'teacher':
            obj.user.role = 'teacher'
            obj.user.save()
        super().save_model(request, obj, form, change)
