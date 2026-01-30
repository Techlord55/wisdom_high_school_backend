# Location: .\apps\payments\services.py
# ==================== apps/payments/services.py ====================
from apps.payments.models import Payment
from apps.students.models import Student
from apps.payments.stripe.client import create_payment_intent
from django.utils import timezone


def create_payment(student: Student, amount: float, description: str, 
                  payment_method: str) -> Payment:
    """Create a payment record."""
    
    payment = Payment.objects.create(
        student=student,
        amount=amount,
        description=description,
        payment_method=payment_method,
        payment_status='pending'
    )
    
    return payment


def create_stripe_payment(payment: Payment):
    """Create Stripe payment intent."""
    
    result = create_payment_intent(
        amount=float(payment.amount),
        payment_id=str(payment.id),
        metadata={
            'student_id': str(payment.student.id),
            'description': payment.description
        }
    )
    
    payment.stripe_payment_intent_id = result['payment_intent_id']
    payment.save()
    
    return result


def complete_payment(payment_id: str, transaction_id: str):
    """Mark payment as completed."""
    
    payment = Payment.objects.get(id=payment_id)
    payment.payment_status = 'completed'
    payment.transaction_id = transaction_id
    payment.paid_at = timezone.now()
    payment.save()
    
    return payment

