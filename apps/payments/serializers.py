# Location: .\apps\payments\serializers.py
# ==================== apps/payments/serializers.py ====================
from rest_framework import serializers
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer."""
    
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'student_name', 'student_id', 'amount',
            'description', 'payment_method', 'payment_status',
            'transaction_id', 'stripe_payment_intent_id', 'paid_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

