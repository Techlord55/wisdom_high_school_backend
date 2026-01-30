# Location: backend/apps/payments/management/commands/create_test_payments.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.students.models import Student
from apps.payments.models import Payment
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create test payment records for a student'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=str,
            help='Student ID (e.g., WHS260002)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Student email',
        )

    def handle(self, *args, **options):
        student_id = options.get('student_id')
        email = options.get('email')
        
        # Find student
        student = None
        if student_id:
            try:
                student = Student.objects.get(student_id=student_id)
                self.stdout.write(f"Found student: {student.student_id} - {student.user.full_name}")
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Student with ID {student_id} not found'))
                return
        elif email:
            try:
                student = Student.objects.get(user__email=email)
                self.stdout.write(f"Found student: {student.student_id} - {student.user.full_name}")
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Student with email {email} not found'))
                return
        else:
            # Get first student
            student = Student.objects.first()
            if not student:
                self.stdout.write(self.style.ERROR('No students found in database'))
                return
            self.stdout.write(f"Using first student: {student.student_id} - {student.user.full_name}")
        
        # Delete existing payments for this student (for testing)
        existing_count = Payment.objects.filter(student=student).count()
        if existing_count > 0:
            Payment.objects.filter(student=student).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {existing_count} existing payments'))
        
        # Create test payments
        payments_data = [
            {
                'amount': Decimal('100000.00'),
                'description': 'First Term - School Fees',
                'payment_method': 'mtn',
                'payment_status': 'completed',
                'transaction_id': 'MTN123456789',
                'paid_at': timezone.now(),
            },
            {
                'amount': Decimal('75000.00'),
                'description': 'Second Term - Partial Payment',
                'payment_method': 'orange',
                'payment_status': 'completed',
                'transaction_id': 'ONG987654321',
                'paid_at': timezone.now(),
            },
            {
                'amount': Decimal('50000.00'),
                'description': 'Library Fees',
                'payment_method': 'cash',
                'payment_status': 'completed',
                'transaction_id': 'CASH001',
                'paid_at': timezone.now(),
            },
        ]
        
        created_payments = []
        for payment_data in payments_data:
            payment = Payment.objects.create(
                student=student,
                **payment_data
            )
            created_payments.append(payment)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created: {payment.description} - {payment.amount} FCFA'
                )
            )
        
        # Calculate totals
        total_paid = sum(p.amount for p in created_payments)
        total_fees = Decimal('350000.00')
        balance = total_fees - total_paid
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(created_payments)} payments'))
        self.stdout.write(f'Student: {student.student_id} - {student.user.full_name}')
        self.stdout.write(f'Total Fees: {total_fees:,.2f} FCFA')
        self.stdout.write(f'Total Paid: {total_paid:,.2f} FCFA')
        self.stdout.write(f'Balance: {balance:,.2f} FCFA')
        self.stdout.write('='*60)
