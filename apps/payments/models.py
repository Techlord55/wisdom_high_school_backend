# Location: .\apps\payments\models.py
# ==================== apps/payments/models.py ====================
from django.db import models
from django.conf import settings  # ADD THIS LINE
from apps.common.models import TimeStampedModel
from apps.students.models import Student


class Payment(TimeStampedModel):
    """Payment tracking model."""
    
    METHOD_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('orange', 'Orange Money'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('stripe', 'Stripe'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.amount} - {self.payment_status}"


class Notification(TimeStampedModel):
    """Notification model."""
    
    # CHANGE THIS LINE - use settings.AUTH_USER_MODEL instead of User
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"