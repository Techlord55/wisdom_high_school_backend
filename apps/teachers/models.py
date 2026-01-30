# ==================== apps/teachers/models.py ====================
from django.db import models
from apps.common.models import TimeStampedModel
from apps.users.models import User


class Teacher(TimeStampedModel):
    """Teacher profile model."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Teaching assignments
    subjects = models.JSONField(default=list, help_text="List of subjects taught")
    classes_assigned = models.JSONField(default=list, help_text="List of classes assigned to teach")
    hours_per_week = models.IntegerField(default=0, help_text="Number of teaching hours per week")
    
    class Meta:
        db_table = 'teachers'
        ordering = ['teacher_id']
    
    def __str__(self):
        return f"{self.teacher_id} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.teacher_id:
            # Auto-generate teacher ID: TCH + Sequential Number
            last_teacher = Teacher.objects.order_by('teacher_id').last()
            
            if last_teacher:
                last_num = int(last_teacher.teacher_id[3:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.teacher_id = f'TCH{str(new_num).zfill(5)}'
        
        super().save(*args, **kwargs)
