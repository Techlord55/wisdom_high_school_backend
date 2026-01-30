# Location: .\apps\payments\views.py
# ==================== apps/payments/views.py ====================
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.students import selectors
from apps.common.permissions import IsStudent, IsTeacherOrAdmin
from apps.common.utils import success_response, error_response


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment viewset."""
    
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            try:
                student = selectors.get_student_by_user(user)
                return Payment.objects.filter(student=student)
            except:
                return Payment.objects.none()
        
        return Payment.objects.all()
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Get current student's payments."""
        try:
            student = selectors.get_student_by_user(request.user)
            payments = Payment.objects.filter(student=student).order_by('-created_at')
            
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        except:
            return error_response('Student profile not found', status=404)

