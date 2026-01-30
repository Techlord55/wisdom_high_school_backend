# ==================== apps/payments/admin.py ====================
from django.contrib import admin
from apps.payments.models import Payment, Notification


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_method', 'payment_status', 
                   'paid_at', 'created_at']
    list_filter = ['payment_method', 'payment_status', 'paid_at']
    search_fields = ['student__student_id', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']